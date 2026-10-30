"""Admin routes for analysing the agent: prompt history with full request traces, and summaries.

The paths and response shapes match what the Admin Console reads, directly under
`/api/admin/observability` and through the console's gateway path. Prompt history contains users'
questions and the agent's decisions, so until administrator sign-in exists these routes answer
only connections from this machine. The check uses the connecting address, never a forwarded
header, which any client could set.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from aria.observability.store import PromptStore
from aria.observability.summary import summarize

router = APIRouter(tags=["observability"])

PREFIXES = ("/api/admin/observability", "/api/admin/console/gateway/api/admin/observability")
LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def local_admin_only(request: Request) -> None:
    host = request.client.host if request.client else None
    if host not in LOOPBACK:
        raise HTTPException(
            status_code=403,
            detail="Agent analytics are limited to this machine until administrator sign-in is configured.",
        )


def prompt_store(request: Request) -> PromptStore:
    return request.app.state.prompt_store


StoreDep = Annotated[PromptStore, Depends(prompt_store)]


def _routes(suffix: str):
    def register(handler):
        for prefix in PREFIXES:
            router.add_api_route(
                prefix + suffix, handler, methods=["GET"], dependencies=[Depends(local_admin_only)]
            )
        return handler

    return register


def _page(items: list, page: int, page_size: int, **extra) -> dict:
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    return {"items": page_items, "total": len(items), "page": page, "pageSize": page_size, **extra}


@_routes("")
async def snapshot(response: Response, store: StoreDep, minutes: int = Query(60, ge=1, le=10080)) -> dict:
    response.headers["Cache-Control"] = "no-store"
    cutoff = time.time() - minutes * 60
    traces = [record["trace"] for record in store.records() if record.get("started", 0) >= cutoff]
    return summarize(traces, minutes)


@_routes("/users")
async def users(
    request: Request,
    response: Response,
    store: StoreDep,
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    counts: dict[str, dict] = {}
    for record in store.records():
        entry = counts.setdefault(
            record["user_key"],
            {"user_key": record["user_key"], "username": record["username"], "subject": record["subject"],
             "prompt_count": 0},
        )  # fmt: skip
        entry["prompt_count"] += 1
    needle = search.lower()
    items = [
        entry for entry in counts.values() if needle in f"{entry['username']} {entry['subject']}".lower()
    ]
    return _page(sorted(items, key=lambda entry: entry["username"]), page, page_size)


@_routes("/prompts")
async def prompts(
    request: Request,
    response: Response,
    store: StoreDep,
    user_key: str | None = None,
    search: str = "",
    workspace: str | None = None,
    status: str | None = None,
    before: float | None = None,
    after: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    config = request.app.state.settings.deployment.observability
    needle = search.lower()
    items = []
    for record in store.records():
        if user_key and record["user_key"] != user_key:
            continue
        if workspace and record.get("workspace") != workspace:
            continue
        if status and record["status"] != status:
            continue
        if before is not None and record["started"] > before:
            continue
        if after is not None and record["started"] < after:
            continue
        if needle and needle not in record["prompt"].lower():
            continue
        # The list stays light; the full trace comes with the detail request.
        items.append({key: value for key, value in record.items() if key not in ("trace", "answer")})
    return _page(items, page, page_size, enabled=config.capture_prompts, retentionDays=config.retention_days)


@_routes("/prompts/{request_id}")
async def prompt_detail(request_id: str, response: Response, store: StoreDep) -> dict:
    response.headers["Cache-Control"] = "no-store"
    record = store.find(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return record


@_routes("/traces/{trace_id}")
async def trace_detail(trace_id: str, response: Response, store: StoreDep) -> dict:
    response.headers["Cache-Control"] = "no-store"
    record = next((item for item in store.records() if item.get("trace_id") == trace_id), None)
    if record is None:
        raise HTTPException(status_code=404, detail="Execution flow not found")
    return record["trace"]
