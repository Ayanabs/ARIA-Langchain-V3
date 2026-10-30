"""A detailed record of one request, for analysing what the agent did and why.

The record has three parts:
- `flow`, `spans` and `modelCalls` in the shape the Admin Console's response analytics reads;
- `issues`: every problem met, explained in plain words (see issues.py);
- `details`: per-stage data, such as the shortlist with scores, the model's raw decision, each
  backend call and how the evidence was packed.
Every event is also written to the JSON log with the trace ID.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any

from aria.observability.issues import Issue, issue

logger = logging.getLogger("aria.trace")

KIND = "query"


class RequestTrace:
    def __init__(
        self, question: str, *, user_key: str, username: str, subject: str = "", workspace: str = ""
    ):
        self.trace_id = uuid.uuid4().hex
        self.request_id = uuid.uuid4().hex
        self.question = question
        self.user_key = user_key
        self.username = username
        self.subject = subject
        self.workspace = workspace
        self.started_at = time.time()
        self._started = time.perf_counter()
        self.status = "running"
        self.route: str | None = None
        self.failure: str | None = None
        self.answer: str | None = None
        self.events: list[dict] = []
        self.spans: list[dict] = []
        self.model_calls: list[dict] = []
        self.issues: list[Issue] = []
        self.details: dict[str, Any] = {}
        self.duration_ms: int | None = None

    def now_ms(self) -> int:
        return round((time.perf_counter() - self._started) * 1000)

    def event(self, event: str, label: str, **fields: Any) -> None:
        """Record one step. Fields use the console's FlowEvent names (camelCase)."""
        record = {"sequence": len(self.events) + 1, "event": event, "label": label, "atMs": self.now_ms()}
        record.update({key: value for key, value in fields.items() if value is not None})
        self.events.append(record)
        logger.info(label, extra={"trace": self.trace_id, "trace_event": event, **_loggable(fields)})

    @contextmanager
    def stage(self, name: str):
        """Time a stage as a span; an exception marks it as an error and propagates."""
        start = self.now_ms()
        status = "ok"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            duration = self.now_ms() - start
            self.spans.append({"stage": name, "startMs": start, "durationMs": duration, "status": status})

    def model_call(
        self, *, role: str, purpose: str, model: str, wall_ms: int | None, prompt_tokens: int | None,
        completion_tokens: int | None, cached_tokens: int | None, estimated_prompt_tokens: int | None,
        error_kind: str | None = None,
    ) -> None:  # fmt: skip
        call = {
            "role": role,
            "model": model,
            "purpose": purpose,
            "client_wall_ms": wall_ms,
            "prompt_eval_count": prompt_tokens,
            "eval_count": completion_tokens,
            "cached_tokens": cached_tokens,
            "estimated_prompt_tokens": estimated_prompt_tokens,
            "error_kind": error_kind,
        }
        self.model_calls.append({key: value for key, value in call.items() if value is not None})
        self.event(
            "model_call",
            f"{purpose.replace('_', ' ').capitalize()} model call",
            role=role,
            model=model,
            durationMs=wall_ms,
            inputTokens=prompt_tokens,
            outputTokens=completion_tokens,
            status="error" if error_kind else "ok",
            errorKind=error_kind,
        )

    def add_issue(self, code: str, stage: str, detail: str = "") -> None:
        found = issue(code, stage, detail)
        self.issues.append(found)
        context = {"trace": self.trace_id, "issue": code, "stage": stage, "detail": detail}
        logger.warning(found.title, extra=context)

    def record(self, stage: str, **data: Any) -> None:
        """Keep structured detail for a stage, shown in full in the analysis view."""
        self.details.setdefault(stage, {}).update(data)

    def finish(self, status: str, failure: str | None = None) -> None:
        self.status = status
        self.failure = failure
        self.duration_ms = self.now_ms()
        self.event(
            "finished", "Request finished", status=status, errorKind=failure, durationMs=self.duration_ms
        )

    def to_console(self) -> dict:
        """The Trace object the Admin Console reads, with ARIA's issues and details added."""
        backend_calls = self.details.get("tool_calls", {}).get("calls", [])
        return {
            "traceId": self.trace_id,
            "startedAt": self.started_at,
            "kind": KIND,
            "status": self.status,
            "report": False,
            "durationMs": self.duration_ms if self.duration_ms is not None else self.now_ms(),
            "route": self.route,
            "failure": self.failure,
            "firstPublishedTokenMs": None,
            "modelCalls": self.model_calls,
            "promptTokensPeak": max(
                (call.get("prompt_eval_count") or 0 for call in self.model_calls), default=None
            ),
            "flow": self.events,
            "spans": self.spans,
            "quality": {
                "sourceCount": sum(1 for call in backend_calls if call.get("status") == "ok"),
                "chartCount": 0,
                "factCount": 0,
                "gapCount": sum(1 for found in self.issues if found.severity != "info"),
                "reviewAttempts": 0,
                "rejectedAttempts": 0,
                "deterministicFailures": sum(1 for found in self.issues if found.severity == "error"),
            },
            "issues": [found.to_dict() for found in self.issues],
            "details": self.details,
        }

    def to_prompt_record(self) -> dict:
        """The prompt-history entry, in the console's Prompt shape, carrying the full trace."""
        return {
            "id": self.request_id,
            "user_key": self.user_key,
            "username": self.username,
            "subject": self.subject,
            "workspace": self.workspace,
            "started": self.started_at,
            "prompt": self.question,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "trace_id": self.trace_id,
            "answer": self.answer,
            "trace": self.to_console(),
        }


def _loggable(fields: dict) -> dict:
    # Log scalars and short lists only; full structures belong in the trace, not every log line.
    def short(value: Any) -> bool:
        return isinstance(value, str | int | float | bool) or (isinstance(value, list) and len(value) <= 20)

    return {key: value for key, value in fields.items() if value is not None and short(value)}
