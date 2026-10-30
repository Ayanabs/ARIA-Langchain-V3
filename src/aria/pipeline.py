"""One question through the request flow: tool search, tool choice, key chain, answer.

Every stage records into the request's trace (see observability/recording.py), so an
administrator can see afterwards what was decided, what was called and what went wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from aria.calling.chain import ChainOutcome, ToolInvoker, run_chain
from aria.calling.selection import ToolSelection, select_tools
from aria.catalog.catalog import ToolCatalog
from aria.catalog.graph import ChainPlan
from aria.logging_setup import trace_id_var
from aria.models.client import ChatModel, ModelError
from aria.observability import recording
from aria.observability.trace import RequestTrace
from aria.prompts import PromptsConfig
from aria.search.lexical import expand_with_producers, rank
from aria.synthesis.answer import EvidencePacket, pack_evidence, write_answer, write_reply

PUBLISHED = "published"
FAILED = "error"


@dataclass
class PipelineResult:
    question: str
    trace: RequestTrace
    answer: str = ""
    shortlist: list[str] = field(default_factory=list)
    selection: ToolSelection | None = None
    plan: ChainPlan | None = None
    outcome: ChainOutcome | None = None
    evidence: EvidencePacket | None = None


async def answer_question(
    question: str,
    *,
    catalog: ToolCatalog,
    tool_model: ChatModel,
    synthesis_model: ChatModel,
    invoke: ToolInvoker,
    prompts: PromptsConfig,
    max_fan_out: int,
    trace: RequestTrace,
) -> PipelineResult:
    """Answer one question. A model failure is recorded in the trace and then raised."""
    result = PipelineResult(question=question, trace=trace)
    token = trace_id_var.set(trace.trace_id)
    try:
        trace.event("received", "Question received", stage="request")
        await _search_and_select(result, catalog, tool_model, prompts)
        await _run_chain(result, catalog, synthesis_model, invoke, max_fan_out)
        await _write_answer(result, synthesis_model, prompts)
        trace.finish(PUBLISHED)
        return result
    except ModelError as error:
        trace.finish(FAILED, failure=error.kind)
        raise
    except Exception as error:
        trace.add_issue("unexpected_error", "request", f"{type(error).__name__}: {error}")
        trace.finish(FAILED, failure="unexpected")
        raise
    finally:
        trace_id_var.reset(token)


async def _search_and_select(result: PipelineResult, catalog, tool_model: ChatModel, prompts) -> None:
    trace = result.trace
    k = tool_model.role.profile.shortlist_k
    with trace.stage("tool_search"):
        ranked = rank(result.question, catalog)
        result.shortlist = expand_with_producers([name for name, _ in ranked[:k]], catalog)
    recording.shortlist(trace, ranked, result.shortlist, k, len(catalog.tools))
    if not result.shortlist:
        return

    with trace.stage("tool_selection"):
        try:
            result.selection = await select_tools(
                result.question,
                result.shortlist,
                catalog,
                tool_model,
                prompts.rendered("tool_selection"),
                date.today().isoformat(),
            )
        except ModelError as error:
            recording.model_failure(trace, tool_model, "tool_selection", error)
            raise
    recording.model_reply(trace, tool_model, "tool_selection", result.selection.reply)
    recording.selection(trace, result.selection)


async def _run_chain(
    result: PipelineResult, catalog, synthesis_model: ChatModel, invoke, max_fan_out
) -> None:
    selection = result.selection
    if not (selection and selection.route == "tools" and selection.goal):
        return
    trace = result.trace
    with trace.stage("key_chain"):
        filled = {tool: set(arguments) for tool, arguments in selection.arguments.items()}
        result.plan = catalog.plan(selection.goal, set(selection.supplied_keys), filled)
        recording.plan(trace, result.plan, catalog)
        result.outcome = await run_chain(
            result.plan,
            catalog.tools,
            invoke=invoke,
            arguments=selection.arguments,
            supplied=selection.supplied_keys,
            max_fan_out=max_fan_out,
        )
    recording.chain(trace, result.outcome, catalog)
    budget = synthesis_model.role.profile.input_budget_tokens
    result.evidence = pack_evidence(selection.goal, result.outcome, budget)
    recording.evidence(trace, result.evidence)


async def _write_answer(result: PipelineResult, synthesis_model: ChatModel, prompts) -> None:
    trace = result.trace
    with trace.stage("synthesis"):
        try:
            if result.evidence is None:
                reply = await write_reply(result.question, synthesis_model, prompts.rendered("conversation"))
            else:
                reply = await write_answer(
                    result.question,
                    result.evidence,
                    synthesis_model,
                    prompts.rendered("synthesis"),
                    date.today().isoformat(),
                )
        except ModelError as error:
            recording.model_failure(trace, synthesis_model, "synthesis", error)
            raise
    recording.model_reply(trace, synthesis_model, "synthesis", reply)
    result.answer = reply.content.strip()
    recording.answer(trace, result.answer)
