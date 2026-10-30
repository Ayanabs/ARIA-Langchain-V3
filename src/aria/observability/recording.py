"""What each pipeline stage records into a request trace.

Kept apart from the pipeline so the flow stays readable. Each function turns one stage's results
into flow events, structured details and, where something went wrong, explained issues.
"""

from __future__ import annotations

from aria.calling.chain import ChainOutcome
from aria.calling.selection import ToolSelection
from aria.catalog.catalog import ToolCatalog
from aria.catalog.graph import ChainPlan
from aria.models.client import ChatModel, ModelError, ModelReply
from aria.observability.trace import RequestTrace
from aria.synthesis.answer import EvidencePacket

# How many ranked tools to keep in the trace beyond the shortlist, to show what nearly made it.
RANKING_SHOWN = 25

MODEL_ERROR_ISSUES = {
    "timeout": "model_timeout",
    "unreachable": "model_unreachable",
    "provider_error": "model_provider_error",
    "context_capacity": "context_capacity",
    "invalid_output": "invalid_output",
    "output_limit": "output_limit",
}

CHAIN_ISSUES = {
    "fan_out_limit": "fan_out_limit",
    "argument_error": "argument_rejected",
    "invented_key": "invented_key",
    "backend_error": "backend_error",
    "no_records": "no_records",
    "missing_key_value": "no_records",
    "ambiguous": "ambiguous_subject",
}


def shortlist(trace: RequestTrace, ranked: list[tuple[str, float]], chosen: list[str], k: int, total: int):
    scores = dict(ranked)
    by_search = [name for name in chosen if name in scores][:k]
    trace.event(
        "tool_search",
        "Tool search",
        stage="tool_search",
        selectedToolCount=len(chosen),
        availableToolCount=total,
        selectedOperations=chosen,
    )
    trace.record(
        "tool_search",
        method="lexical BM25 over tool names, descriptions and parameters",
        shortlist_size=k,
        ranking=[{"tool": name, "score": round(score, 3)} for name, score in ranked[:RANKING_SHOWN]],
        shortlisted_by_search=by_search,
        added_as_key_producers=[name for name in chosen if name not in by_search],
    )
    if not chosen:
        trace.add_issue("no_tools_shortlisted", "tool_search", "No tool shares a word with the question.")


def model_reply(trace: RequestTrace, model: ChatModel, purpose: str, reply: ModelReply) -> None:
    trace.model_call(
        role=model.role.role,
        purpose=purpose,
        model=model.role.name,
        wall_ms=reply.wall_ms,
        prompt_tokens=reply.prompt_tokens,
        completion_tokens=reply.completion_tokens,
        cached_tokens=reply.cached_tokens,
        estimated_prompt_tokens=reply.estimated_prompt_tokens,
    )


def model_failure(trace: RequestTrace, model: ChatModel, purpose: str, error: ModelError) -> None:
    trace.model_call(
        role=model.role.role,
        purpose=purpose,
        model=model.role.name,
        wall_ms=None,
        prompt_tokens=None,
        completion_tokens=None,
        cached_tokens=None,
        estimated_prompt_tokens=None,
        error_kind=error.kind,
    )
    code = MODEL_ERROR_ISSUES.get(error.kind, "unexpected_error")
    trace.add_issue(code, purpose, _model_error_detail(error))


def _model_error_detail(error: ModelError) -> str:
    detail = str(error)
    # 520-530 are sent by the tunnel or proxy in front of the model host, not by the host itself.
    if error.status_code is not None and 520 <= error.status_code <= 530:
        detail += (
            ". This status comes from the tunnel in front of the model host: the host itself is down or "
            "the tunnel cannot reach it."
        )
    return detail


def selection(trace: RequestTrace, chosen: ToolSelection) -> None:
    trace.route = "database" if chosen.route == "tools" else "conversation"
    trace.event(
        "tool_selection",
        f"Chose {chosen.goal}" if chosen.goal else "No tool needed",
        stage="tool_selection",
        route=trace.route,
        operation=chosen.goal,
        argumentNames=sorted({name for args in chosen.arguments.values() for name in args}),
    )
    trace.record(
        "tool_selection",
        model_decision=chosen.reply.content if chosen.reply else None,
        route=chosen.route,
        goal_tool=chosen.goal,
        arguments=chosen.arguments,
        supplied_keys={
            key_id: {"values": list(value.values), "source": value.source}
            for key_id, value in chosen.supplied_keys.items()
        },
        rejected=chosen.rejected,
    )
    for reason in chosen.rejected:
        trace.add_issue("argument_rejected", "tool_selection", reason)
    if chosen.route != "tools":
        trace.add_issue("answered_without_tools", "tool_selection")


def plan(trace: RequestTrace, planned: ChainPlan, catalog: ToolCatalog) -> None:
    trace.event(
        "plan",
        f"Planned {len(planned.steps)} call(s)" if planned.complete else "Plan incomplete",
        stage="key_chain",
        status="ok" if planned.complete else "incomplete",
        selectedOperations=[step.tool for step in planned.steps],
    )
    trace.record(
        "plan",
        complete=planned.complete,
        steps=[{"tool": step.tool, "keys_from": dict(step.key_sources)} for step in planned.steps],
        missing_keys=[_key_label(catalog, key_id) for key_id in planned.missing_keys],
        cycle=list(planned.cycle),
        too_deep=planned.too_deep,
    )
    if planned.missing_keys:
        labels = ", ".join(_key_label(catalog, key_id) for key_id in planned.missing_keys)
        trace.add_issue("missing_key", "key_chain", f"{planned.goal} needs: {labels}")
    if planned.cycle:
        trace.add_issue("dependency_cycle", "key_chain", " -> ".join(planned.cycle))
    if planned.too_deep:
        trace.add_issue("chain_too_deep", "key_chain", f"while planning {planned.goal}")


def chain(trace: RequestTrace, outcome: ChainOutcome, catalog: ToolCatalog) -> None:
    calls = []
    for call in outcome.calls:
        tool = catalog.tools.get(call.tool)
        operation = tool.operation.label if tool else call.tool
        failed = call.error is not None
        trace.event(
            "tool_call",
            f"Called {call.tool}",
            stage="tool_calls",
            operation=operation,
            durationMs=call.duration_ms,
            recordCount=len(call.rows),
            status="error" if failed else "ok",
            errorKind=f"http_{call.status_code}" if call.status_code else ("error" if failed else None),
        )
        calls.append(
            {
                "tool": call.tool,
                "operation": operation,
                "arguments": call.arguments,
                "key_sources": call.key_sources,
                "records": len(call.rows),
                "fields": sorted(call.rows[0]) if call.rows else [],
                "duration_ms": call.duration_ms,
                "status": "error" if failed else "ok",
                "status_code": call.status_code,
                "error": call.error,
            }
        )
    trace.record(
        "tool_calls",
        status=outcome.status,
        kind=outcome.kind,
        reason=outcome.reason,
        calls=calls,
        goal_records=len(outcome.goal_rows),
        candidates=len(outcome.candidates),
    )
    code = CHAIN_ISSUES.get(outcome.kind or "")
    if code:
        trace.add_issue(code, "tool_calls", outcome.reason or "")


def evidence(trace: RequestTrace, packet: EvidencePacket) -> None:
    trace.event("evidence", "Packed evidence", stage="synthesis", recordCount=packet.shown_rows)
    trace.record("evidence", total_records=packet.total_rows, shown_records=packet.shown_rows)
    if packet.shown_rows < packet.total_rows:
        trace.add_issue(
            "evidence_truncated", "synthesis", f"{packet.shown_rows} of {packet.total_rows} records shown"
        )


def answer(trace: RequestTrace, text: str) -> None:
    trace.answer = text
    trace.record("answer", characters=len(text))


def _key_label(catalog: ToolCatalog, key_id: str) -> str:
    key = catalog.keys.get(key_id)
    return f"{key.label} ({key_id})" if key else key_id
