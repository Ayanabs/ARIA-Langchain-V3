"""Chat shapes, matching the fields the frontend reads (camelCase, as the previous chat API sent)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatSummary(_CamelModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class CreatedChat(ChatSummary):
    """A new chat, with the fields that let the frontend add it to its list without re-fetching."""

    message_count: int = 0
    is_new: bool = True


class ChatMessage(_CamelModel):
    id: int
    sender: str  # "user" or "agent"
    content: str | None = None
    results: list[dict[str, Any]] | None = None
    endpoint_results: list[dict[str, Any]] | None = None
    progress_steps: list[dict[str, Any]] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    trace_id: str | None = None
    chart: Any = None
    error: str | None = None
    execution_time_ms: int | None = None
    server_time_ms: int | None = None
    server_time: str | None = None
    client_duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    created_at: datetime


class ChatDetails(_CamelModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage]


class TitleRequest(_CamelModel):
    title: str | None = None


class MetricsRequest(_CamelModel):
    client_duration_ms: int | None = None
    server_time_ms: int | None = None
