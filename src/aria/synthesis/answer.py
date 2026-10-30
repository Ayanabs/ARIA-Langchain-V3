"""Step 5: pack the evidence within budget and have the synthesis model write the answer.

Full rows stay in code. The model sees a compact packet: which tool produced the records, how many
there are (counted in code), and as many rows as fit the budget, with the packet saying plainly when
it shows only some of them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from aria.calling.chain import ChainOutcome
from aria.models.client import BYTES_PER_TOKEN_ESTIMATE, ChatModel, ModelReply

# Room kept for the instructions and the question when sizing the evidence.
PROMPT_OVERHEAD_TOKENS = 600


@dataclass(frozen=True)
class EvidencePacket:
    text: str
    total_rows: int
    shown_rows: int


def pack_evidence(goal: str, outcome: ChainOutcome, budget_tokens: int) -> EvidencePacket:
    rows = outcome.goal_rows
    if outcome.status != "complete":
        text = f"No data was retrieved. Status: {outcome.status}. Reason: {outcome.reason}."
        if outcome.candidates:
            text += f" {len(outcome.candidates)} records matched:\n" + _rows_text(outcome.candidates)
        return EvidencePacket(text=text, total_rows=0, shown_rows=0)

    budget_bytes = max(budget_tokens - PROMPT_OVERHEAD_TOKENS, 0) * BYTES_PER_TOKEN_ESTIMATE
    shown = []
    used = 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, default=str)
        if used + len(line.encode("utf-8")) > budget_bytes:
            break
        shown.append(row)
        used += len(line.encode("utf-8")) + 1
    header = f"Source S1: {goal}, {len(rows)} records in total"
    if len(shown) < len(rows):
        header += f"; only the first {len(shown)} are shown, so do not total or count from these rows"
    return EvidencePacket(text=f"{header}.\n{_rows_text(shown)}", total_rows=len(rows), shown_rows=len(shown))


def _rows_text(rows: list[dict]) -> str:
    return "\n".join(json.dumps(row, ensure_ascii=False, default=str) for row in rows)


async def write_answer(
    question: str, evidence: EvidencePacket, model: ChatModel, instructions: str, today: str
) -> ModelReply:
    request = f"Evidence:\n{evidence.text}\n\nToday's date: {today}\nQuestion: {question}"
    messages = [{"role": "system", "content": instructions}, {"role": "user", "content": request}]
    return await model.complete(messages, temperature=0.2)


async def write_reply(question: str, model: ChatModel, instructions: str) -> ModelReply:
    """A conversational reply when no records are needed."""
    messages = [{"role": "system", "content": instructions}, {"role": "user", "content": question}]
    return await model.complete(messages, temperature=0.3)
