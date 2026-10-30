"""Summaries over recent request traces, in the Admin Console's snapshot shape.

Besides the console's latency and outcome figures, `issues` counts each kind of problem met, so
recurring causes stand out.
"""

from __future__ import annotations

import time
from collections import Counter

# Traces listed in a snapshot; the prompt history has them all.
TRACES_LISTED = 50


def distribution(values: list[float]) -> dict:
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "p50Ms": None, "p95Ms": None, "p99Ms": None}

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    return {
        "count": len(ordered),
        "p50Ms": percentile(0.5),
        "p95Ms": percentile(0.95),
        "p99Ms": percentile(0.99),
    }


def summarize(traces: list[dict], minutes: int) -> dict:
    stages: dict[str, list[float]] = {}
    for trace in traces:
        for span in trace.get("spans", []):
            stages.setdefault(span["stage"], []).append(span["durationMs"])

    models: dict[str, dict] = {}
    for trace in traces:
        for call in trace.get("modelCalls", []):
            entry = models.setdefault(call["role"], {"calls": 0, "client_wall_ms": 0, "eval_count": 0})
            entry["calls"] += 1
            entry["client_wall_ms"] += call.get("client_wall_ms") or 0
            entry["eval_count"] += call.get("eval_count") or 0

    issues = Counter(found["code"] for trace in traces for found in trace.get("issues", []))
    published = [trace for trace in traces if trace["status"] == "published"]
    return {
        "observedAt": time.time(),
        "windowMinutes": minutes,
        "requestCount": len(traces),
        "outcomes": dict(Counter(trace["status"] for trace in traces)),
        "latency": distribution([trace["durationMs"] for trace in traces]),
        "publishedLatency": distribution([trace["durationMs"] for trace in published]),
        "stages": {stage: distribution(values) for stage, values in stages.items()},
        "model": models,
        "capacity": {
            "activeRequestsThisWorker": 0,
            "traceWriteErrorsThisWorker": 0,
            "peakObservedContextUsage": max(
                (trace.get("promptTokensPeak") or 0 for trace in traces), default=None
            ),
            "note": "Prompt sizes are the model host's own token counts.",
        },
        "reports": {"total": 0, "published": 0, "withheld": 0, "rejectedDrafts": 0, "withGaps": 0},
        "traces": traces[:TRACES_LISTED],
        "traceListTruncated": len(traces) > TRACES_LISTED,
        "stageTiming": "Stage durations measured inside ARIA for each request.",
        "issues": dict(issues.most_common()),
    }
