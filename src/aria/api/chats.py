"""Chat routes, compatible with what the frontend calls (`/api/chats...`, also under `/api/gateway`).

Every route acts only on the caller's own chats. A chat that does not exist and one that belongs to
someone else both answer 404, so chat IDs cannot be probed.
"""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from aria.auth.caller import Caller, current_caller
from aria.chats.models import ChatDetails, ChatSummary, CreatedChat, MetricsRequest, TitleRequest
from aria.chats.store import ChatLimitReached, ChatStore

router = APIRouter(tags=["chats"])

# The frontend reaches these through its gateway proxy, and the previous service also answered on the
# prefixed paths, so both are kept.
PREFIXES = ("/api/chats", "/api/gateway/chats", "/api/gateway/api/chats")

CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def chat_store(request: Request) -> ChatStore:
    return request.app.state.chat_store


CallerDep = Annotated[Caller, Depends(current_caller)]
StoreDep = Annotated[ChatStore, Depends(chat_store)]


def clean_title(request: Request, title: str | None) -> str:
    config = request.app.state.settings.deployment.chats
    text = " ".join(CONTROL_CHARACTERS.sub(" ", title or "").split()) or config.default_title
    if len(text) > config.max_title_length:
        text = text[: config.max_title_length - 3] + "..."
    return text


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Chat not found")


def _routes(method: str, suffix: str = ""):
    """Register one handler on the path under every prefix."""

    def register(handler):
        for prefix in PREFIXES:
            router.add_api_route(prefix + suffix, handler, methods=[method], response_model_by_alias=True)
        return handler

    return register


@_routes("GET")
async def list_chats(caller: CallerDep, store: StoreDep) -> list[ChatSummary]:
    return store.list_chats(caller.user_id)


@_routes("POST")
async def create_chat(
    request: Request,
    caller: CallerDep,
    store: StoreDep,
    body: TitleRequest | None = None,
) -> CreatedChat:
    try:
        created = store.create_chat(caller.user_id, clean_title(request, body.title if body else None))
    except ChatLimitReached as error:
        raise HTTPException(status_code=429, detail="Chat limit reached; delete a chat first") from error
    return CreatedChat(**created.model_dump())


@_routes("GET", "/{chat_id}")
async def get_chat(chat_id: int, caller: CallerDep, store: StoreDep) -> ChatDetails:
    chat = store.get_chat(caller.user_id, chat_id)
    if chat is None:
        raise _not_found()
    return chat


@_routes("PUT", "/{chat_id}")
async def rename_chat(
    chat_id: int,
    request: Request,
    body: TitleRequest,
    caller: CallerDep,
    store: StoreDep,
) -> ChatSummary:
    renamed = store.rename_chat(caller.user_id, chat_id, clean_title(request, body.title))
    if renamed is None:
        raise _not_found()
    return renamed


@_routes("DELETE", "/{chat_id}")
async def delete_chat(chat_id: int, caller: CallerDep, store: StoreDep) -> JSONResponse:
    if not store.delete_chat(caller.user_id, chat_id):
        raise _not_found()
    return JSONResponse({"status": "deleted"})


@_routes("POST", "/{chat_id}/metrics")
async def record_metrics(
    chat_id: int,
    body: MetricsRequest,
    caller: CallerDep,
    store: StoreDep,
) -> JSONResponse:
    if not store.record_metrics(caller.user_id, chat_id, body.client_duration_ms, body.server_time_ms):
        raise _not_found()
    return JSONResponse({"status": "recorded", "id": chat_id})
