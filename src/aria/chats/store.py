"""Chat storage behind one interface, so a database store can replace the in-memory one.

Every operation takes the owner. A chat that does not exist and a chat owned by someone else look
the same to the caller (None), so a user cannot learn which chat IDs exist.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from aria.chats.models import ChatDetails, ChatMessage, ChatSummary


class ChatLimitReached(Exception):
    """The owner already has the configured maximum number of chats."""


class ChatStore(Protocol):
    def list_chats(self, owner: str) -> list[ChatSummary]: ...
    def create_chat(self, owner: str, title: str) -> ChatSummary: ...
    def get_chat(self, owner: str, chat_id: int) -> ChatDetails | None: ...
    def rename_chat(self, owner: str, chat_id: int, title: str) -> ChatSummary | None: ...
    def delete_chat(self, owner: str, chat_id: int) -> bool: ...
    def record_metrics(
        self, owner: str, chat_id: int, client_duration_ms: int | None, server_time_ms: int | None
    ) -> bool: ...


@dataclass
class _Chat:
    id: int
    owner: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage] = field(default_factory=list)

    def summary(self) -> ChatSummary:
        return ChatSummary(
            id=self.id, title=self.title, created_at=self.created_at, updated_at=self.updated_at
        )


class InMemoryChatStore:
    """Chats kept in process memory: lost on restart, bounded per owner."""

    def __init__(self, max_chats_per_owner: int):
        self.max_chats_per_owner = max_chats_per_owner
        self._chats: dict[int, _Chat] = {}
        self._ids = itertools.count(1)

    def list_chats(self, owner: str) -> list[ChatSummary]:
        owned = [chat for chat in self._chats.values() if chat.owner == owner]
        return [chat.summary() for chat in sorted(owned, key=lambda chat: chat.updated_at, reverse=True)]

    def create_chat(self, owner: str, title: str) -> ChatSummary:
        if sum(1 for chat in self._chats.values() if chat.owner == owner) >= self.max_chats_per_owner:
            raise ChatLimitReached(owner)
        now = datetime.now()
        chat = _Chat(id=next(self._ids), owner=owner, title=title, created_at=now, updated_at=now)
        self._chats[chat.id] = chat
        return chat.summary()

    def get_chat(self, owner: str, chat_id: int) -> ChatDetails | None:
        chat = self._owned(owner, chat_id)
        if chat is None:
            return None
        return ChatDetails(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            messages=list(chat.messages),
        )

    def rename_chat(self, owner: str, chat_id: int, title: str) -> ChatSummary | None:
        chat = self._owned(owner, chat_id)
        if chat is None:
            return None
        chat.title = title
        chat.updated_at = datetime.now()
        return chat.summary()

    def delete_chat(self, owner: str, chat_id: int) -> bool:
        if self._owned(owner, chat_id) is None:
            return False
        del self._chats[chat_id]
        return True

    def record_metrics(
        self, owner: str, chat_id: int, client_duration_ms: int | None, server_time_ms: int | None
    ) -> bool:
        """Attach timings measured by the client to the chat's latest answer."""
        chat = self._owned(owner, chat_id)
        if chat is None:
            return False
        answers = [message for message in chat.messages if message.sender == "agent"]
        if answers:
            if client_duration_ms is not None:
                answers[-1].client_duration_ms = client_duration_ms
            if server_time_ms is not None:
                answers[-1].server_time_ms = server_time_ms
        return True

    def _owned(self, owner: str, chat_id: int) -> _Chat | None:
        chat = self._chats.get(chat_id)
        return chat if chat is not None and chat.owner == owner else None
