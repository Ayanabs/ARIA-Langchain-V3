"""Run a planned key chain: call the producers first, select subjects, pass their keys on.

Given a plan C -> B -> A, the runner calls C with the arguments taken from the user's words,
selects the requested record from C's results, reads the key B needs from it, calls B, and so on
until A. Key arguments are filled only from supplied values (prompt or caller, checked in
`provenance.py`) or from the selected rows of an earlier step; a key argument arriving any other way
stops the chain with the reason.
"""

from __future__ import annotations

import asyncio
import itertools
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from aria.calling.provenance import KeyValue, result_source
from aria.calling.requests import ArgumentError, BackendRequest, build_request, coerce_key_value
from aria.catalog.graph import ChainPlan, ChainStep
from aria.catalog.validation import CatalogTool

ToolInvoker = Callable[[CatalogTool, BackendRequest], Awaitable[Any]]


@dataclass(frozen=True)
class Selection:
    rows: tuple[dict, ...] = ()
    ambiguous: bool = False


SubjectSelector = Callable[[CatalogTool, list[dict]], Selection]


def select_single_subject(tool: CatalogTool, rows: list[dict]) -> Selection:
    """Use a producer's result only when it identifies exactly one record; otherwise ask the user.

    Choosing one of several matches would pick an identifier from a name match, so it is never done.
    """
    if len(rows) > 1:
        return Selection(ambiguous=True)
    return Selection(rows=tuple(rows))


@dataclass
class CallRecord:
    tool: str
    arguments: dict[str, Any]
    # Tool parameter -> where its key value came from.
    key_sources: dict[str, str] = field(default_factory=dict)
    rows: list[dict] = field(default_factory=list)
    error: str | None = None
    duration_ms: int | None = None
    # HTTP status of a failed backend call, when there was a response.
    status_code: int | None = None


@dataclass
class ChainOutcome:
    status: str  # "complete", "needs_clarification", "missing" or "failed"
    # Why the chain stopped, as a stable label: "incomplete_plan", "fan_out_limit", "argument_error",
    # "invented_key", "backend_error", "no_records", "missing_key_value" or "ambiguous".
    kind: str | None = None
    calls: list[CallRecord] = field(default_factory=list)
    goal_rows: list[dict] = field(default_factory=list)
    reason: str | None = None
    # When status is "needs_clarification": the step whose results matched several records.
    clarify_tool: str | None = None
    candidates: list[dict] = field(default_factory=list)


class _StopChain(Exception):
    def __init__(self, outcome: ChainOutcome):
        self.outcome = outcome


async def run_chain(
    plan: ChainPlan,
    tools: Mapping[str, CatalogTool],
    *,
    invoke: ToolInvoker,
    arguments: Mapping[str, Mapping[str, Any]] | None = None,
    supplied: Mapping[str, KeyValue] | None = None,
    select: SubjectSelector = select_single_subject,
    max_fan_out: int = 20,
) -> ChainOutcome:
    """Run every step of `plan` in order.

    `arguments` holds, per tool, the non-key arguments taken from the user's words.
    """
    if not plan.complete:
        return ChainOutcome(status="missing", kind="incomplete_plan", reason=_describe_incomplete_plan(plan))

    runner = _ChainRunner(plan, tools, invoke, arguments or {}, supplied or {}, select, max_fan_out)
    try:
        await runner.run()
    except _StopChain as stop:
        stop.outcome.calls = runner.calls
        return stop.outcome
    return ChainOutcome(status="complete", calls=runner.calls, goal_rows=runner.goal_rows)


class _ChainRunner:
    def __init__(self, plan, tools, invoke, arguments, supplied, select, max_fan_out):
        self.plan = plan
        self.tools = tools
        self.invoke = invoke
        self.arguments = arguments
        self.supplied = supplied
        self.select = select
        self.max_fan_out = max_fan_out
        self.calls: list[CallRecord] = []
        self.selected_rows: dict[str, list[dict]] = {}
        self.goal_rows: list[dict] = []

    async def run(self) -> None:
        # Checked for every step before the first call, so a chain with an invented key reads nothing.
        for step in self.plan.steps:
            self._reject_invented_keys(self.tools[step.tool])
        for step in self.plan.steps:
            tool = self.tools[step.tool]
            call_arguments = self._call_arguments(tool, step)
            results = await asyncio.gather(
                *(self._call(tool, args, sources) for args, sources in call_arguments)
            )
            if step.tool == self.plan.goal:
                self.goal_rows = [row for rows in results for row in rows]
            else:
                self.selected_rows[step.tool] = self._select(tool, results)

    def _call_arguments(self, tool: CatalogTool, step: ChainStep) -> list[tuple[dict, dict]]:
        """One argument set per combination of key values (several when subjects were selected)."""
        base = dict(self.arguments.get(tool.name, {}))
        per_key_options = []
        for key_id, parameters in tool.consumes.items():
            options = self._key_options(tool, step, key_id)
            if options is None:
                continue
            per_key_options.append([(parameters, values, source) for values, source in options])

        combinations = 1
        for options in per_key_options:
            combinations *= len(options)
        if combinations > self.max_fan_out:
            raise _StopChain(
                ChainOutcome(
                    status="failed",
                    kind="fan_out_limit",
                    reason=f"{tool.name} would need {combinations} calls; the limit is {self.max_fan_out}",
                )
            )

        argument_sets = []
        for combination in itertools.product(*per_key_options):
            arguments = dict(base)
            sources = {}
            for parameters, values, source in combination:
                for parameter_name, value in zip(parameters, values, strict=True):
                    parameter = tool.declaration.parameter(parameter_name)
                    try:
                        arguments[parameter_name] = coerce_key_value(value, parameter.type)
                    except ArgumentError as error:
                        raise _StopChain(
                            ChainOutcome(
                                status="failed",
                                kind="argument_error",
                                reason=f"{tool.name}.{parameter_name}: {error}",
                            )
                        ) from error
                    sources[parameter_name] = source
            argument_sets.append((arguments, sources))
        return argument_sets

    def _reject_invented_keys(self, tool: CatalogTool) -> None:
        invented = sorted(set(self.arguments.get(tool.name, {})) & tool.key_parameters)
        if invented:
            raise _StopChain(
                ChainOutcome(
                    status="failed",
                    kind="invented_key",
                    reason=(
                        f"{tool.name}: key arguments {', '.join(invented)} must come from an earlier "
                        "result, the prompt or the caller's identity"
                    ),
                )
            )

    def _key_options(self, tool: CatalogTool, step: ChainStep, key_id: str) -> list | None:
        """The values available for one consumed key, or None when it is optional and unknown."""
        if key_id in self.supplied:
            supplied = self.supplied[key_id]
            return [(supplied.values, supplied.source)]
        producer_name = step.key_sources.get(key_id)
        if producer_name is None:
            return None
        producer = self.tools[producer_name]
        response_fields = producer.produces[key_id]
        options = []
        for row in self.selected_rows.get(producer_name, []):
            values = tuple(_field_value(row, name) for name in response_fields)
            if any(value is None for value in values):
                continue
            if values not in [existing for existing, _ in options]:
                options.append((values, result_source(producer_name)))
        if not options:
            raise _StopChain(
                ChainOutcome(
                    status="missing",
                    kind="missing_key_value",
                    reason=f"{producer_name} returned no {key_id} value for {tool.name}",
                )
            )
        return options

    async def _call(self, tool: CatalogTool, arguments: dict, key_sources: dict) -> list[dict]:
        record = CallRecord(tool=tool.name, arguments=arguments, key_sources=key_sources)
        self.calls.append(record)
        started = time.perf_counter()
        try:
            request = build_request(tool, arguments)
            response = await self.invoke(tool, request)
        except ArgumentError as error:
            record.error = str(error)
            outcome = ChainOutcome(status="failed", kind="argument_error", reason=str(error))
            raise _StopChain(outcome) from error
        except Exception as error:
            record.error = f"{type(error).__name__}: {error}"
            record.status_code = getattr(error, "status_code", None)
            reason = f"{tool.name} failed: {record.error}"
            raise _StopChain(ChainOutcome(status="failed", kind="backend_error", reason=reason)) from error
        finally:
            record.duration_ms = round((time.perf_counter() - started) * 1000)
        record.rows = rows_from_response(response)
        return record.rows

    def _select(self, tool: CatalogTool, results: list[list[dict]]) -> list[dict]:
        # Each call is for one subject, so selection runs per call rather than over the merged rows.
        selected = []
        for rows in results:
            if not rows:
                continue
            selection = self.select(tool, rows)
            if selection.ambiguous:
                raise _StopChain(
                    ChainOutcome(
                        status="needs_clarification",
                        kind="ambiguous",
                        reason=f"{tool.name} matched {len(rows)} records",
                        clarify_tool=tool.name,
                        candidates=rows,
                    )
                )
            selected.extend(selection.rows)
        if not selected:
            reason = f"{tool.name} returned no matching records"
            raise _StopChain(ChainOutcome(status="missing", kind="no_records", reason=reason))
        return selected


def rows_from_response(response: Any) -> list[dict]:
    """Normalise a backend response to a list of records."""
    if response is None:
        return []
    if isinstance(response, list):
        return [item if isinstance(item, dict) else {"value": item} for item in response]
    if isinstance(response, dict):
        return [response]
    return [{"value": response}]


def _field_value(row: dict, dotted_name: str) -> Any:
    value: Any = row
    for part in dotted_name.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _describe_incomplete_plan(plan: ChainPlan) -> str:
    if plan.missing_keys:
        keys = ", ".join(plan.missing_keys)
        return f"{plan.goal} needs {keys}, which no tool produces and the request did not give"
    if plan.cycle:
        return f"{plan.goal} depends on itself: {' -> '.join(plan.cycle)}"
    return f"{plan.goal} needs a longer key chain than the configured limit"
