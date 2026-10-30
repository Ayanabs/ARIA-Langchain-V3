"""Who is calling. Every route that touches a user's data gets the caller from here.

Authentication is not built yet, so every request is attributed to one configured local identity.
That is only safe on a trusted local machine; adding authentication replaces `current_caller` and
nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class Caller:
    user_id: str
    # The caller's own bearer token, passed through unchanged to the backend, which checks it.
    authorization: str | None = None


def current_caller(request: Request) -> Caller:
    settings = request.app.state.settings
    return Caller(
        user_id=settings.deployment.chats.unauthenticated_user_id,
        authorization=request.headers.get("authorization"),
    )
