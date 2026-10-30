"""One question through the request flow: shortlist, tool choice, key chain, answer."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date

from aria.calling.chain import ChainOutcome, ToolInvoker, run_chain
from aria.calling.selection import ToolSelection, select_tools
from aria.catalog.catalog import ToolCatalog
from aria.catalog.graph import ChainPlan
from aria.models.client import ChatModel, ModelReply
from aria.prompts import PromptsConfig
from aria.search.lexical import shortlist as lexical_shortlist
from aria.synthesis.answer import EvidencePacket, pack_evidence, write_answer, write_reply


@dataclass
class StepTrace:
    step: str
    wall_ms: int
    detail: dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    question: str
    answer: str = ""
    shortlist: list[str] = field(default_factory=list)
    selection: ToolSelection | None = None
    plan: ChainPlan | None = None
    outcome: ChainOutcome | None = None
    evidence: EvidencePacket | None = None
    steps: list[StepTrace] = field(default_factory=list)


async def answer_question(
    question: str,
    *,
    catalog: ToolCatalog,
    tool_model: ChatModel,
    synthesis_model: ChatModel,
    invoke: ToolInvoker,
    prompts: PromptsConfig,
    max_fan_out: int,
) -> PipelineResult:
    result = PipelineResult(question=question)
    today = date.today().isoformat()

    started = time.perf_counter()
    result.shortlist = lexical_shortlist(question, catalog, tool_model.role.profile.shortlist_k)
    result.steps.append(StepTrace("shortlist", _since(started), {"tools": len(result.shortlist)}))

    if result.shortlist:
        selection = await select_tools(
            question,
            result.shortlist,
            catalog,
            tool_model,
            prompts.rendered("tool_selection"),
            today,
        )
        result.selection = selection
        result.steps.append(_model_step("tool_selection", selection.reply))

    selection = result.selection
    if selection and selection.route == "tools" and selection.goal:
        started = time.perf_counter()
        filled = {tool: set(arguments) for tool, arguments in selection.arguments.items()}
        result.plan = catalog.plan(selection.goal, set(selection.supplied_keys), filled)
        result.outcome = await run_chain(
            result.plan,
            catalog.tools,
            invoke=invoke,
            arguments=selection.arguments,
            supplied=selection.supplied_keys,
            max_fan_out=max_fan_out,
        )
        result.steps.append(
            StepTrace(
                "tool_calls",
                _since(started),
                {"status": result.outcome.status, "calls": len(result.outcome.calls)},
            )
        )
        budget = synthesis_model.role.profile.input_budget_tokens
        result.evidence = pack_evidence(selection.goal, result.outcome, budget)

    if result.evidence is None:
        reply = await write_reply(question, synthesis_model, prompts.rendered("conversation"))
    else:
        reply = await write_answer(
            question, result.evidence, synthesis_model, prompts.rendered("synthesis"), today
        )
    result.answer = reply.content.strip()
    result.steps.append(_model_step("synthesis", reply))
    return result


def _since(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def _model_step(name: str, reply: ModelReply | None) -> StepTrace:
    if reply is None:
        return StepTrace(name, 0)
    return StepTrace(
        name,
        reply.wall_ms,
        {
            "prompt_tokens": reply.prompt_tokens,
            "estimated_prompt_tokens": reply.estimated_prompt_tokens,
            "completion_tokens": reply.completion_tokens,
            "cached_tokens": reply.cached_tokens,
        },
    )
