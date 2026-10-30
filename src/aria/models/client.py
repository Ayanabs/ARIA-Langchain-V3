"""Chat model access through the provider's OpenAI-compatible API.

Every call is budgeted before it is sent, has its own timeout, and reports wall time and the
provider's own token counters. Only connection failures are retried: a request the host received
is never sent twice.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Any

import httpx

from aria.settings import HttpConfig, ModelRole

# No tokenizer endpoint is exposed, so prompt size is estimated conservatively. Tokenizers for the
# deployed models average well over 3 bytes of UTF-8 per token on mixed text, so this overestimates
# and a prompt that passes the check fits.
BYTES_PER_TOKEN_ESTIMATE = 3


class ModelError(Exception):
    """A model call failed. `kind` is a stable label for traces and error events."""

    def __init__(self, kind: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code


@dataclass(frozen=True)
class ModelReply:
    content: str
    tool_calls: list[dict]
    prompt_tokens: int | None
    completion_tokens: int | None
    # From the provider's counters only; None means the provider did not say.
    cached_tokens: int | None
    estimated_prompt_tokens: int
    wall_ms: int

    def json(self) -> Any:
        try:
            return json.loads(self.content)
        except ValueError as error:
            raise ModelError("invalid_output", "model output is not valid JSON") from error


def estimate_tokens(messages: list[dict], extra: Any = None) -> int:
    text = json.dumps(messages, ensure_ascii=False)
    if extra is not None:
        text += json.dumps(extra, ensure_ascii=False)
    return math.ceil(len(text.encode("utf-8")) / BYTES_PER_TOKEN_ESTIMATE)


class ChatModel:
    def __init__(
        self,
        role: ModelRole,
        http: HttpConfig,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if role.profile.provider != "llama_cpp":
            # The Ollama native-API adapter is not built yet; failing here beats sending requests
            # whose context length the host would silently ignore.
            raise ModelError("unsupported_provider", f"no adapter for provider {role.profile.provider}")
        self.role = role
        self.retries = http.retries
        self.connect_timeout = http.connect_timeout_seconds
        self.transport = transport

    async def complete(
        self,
        messages: list[dict],
        *,
        schema: dict | None = None,
        schema_name: str = "answer",
        max_tokens: int | None = None,
        temperature: float = 0.0,
    ) -> ModelReply:
        profile = self.role.profile
        max_tokens = min(max_tokens or profile.max_output_tokens, profile.max_output_tokens)
        estimated = estimate_tokens(messages, schema)
        if estimated > profile.input_budget_tokens:
            raise ModelError(
                "context_capacity",
                f"prompt needs about {estimated} tokens; the {self.role.role} model's budget is "
                f"{profile.input_budget_tokens}",
            )

        body: dict[str, Any] = {
            "model": self.role.name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": profile.thinking},
        }
        if schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            }
        started = time.perf_counter()
        response = await self._post(body)
        wall_ms = round((time.perf_counter() - started) * 1000)
        return self._read_reply(response, estimated, wall_ms)

    async def _post(self, body: dict) -> httpx.Response:
        headers = {}
        if self.role.api_key and self.role.api_key.get_secret_value():
            headers["Authorization"] = f"Bearer {self.role.api_key.get_secret_value()}"
        timeout = httpx.Timeout(self.role.profile.timeout_seconds, connect=self.connect_timeout)
        url = self.role.api_base.rstrip("/") + "/chat/completions"
        attempts = self.retries + 1
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            for attempt in range(1, attempts + 1):
                try:
                    response = await client.post(url, json=body, headers=headers)
                    break
                except httpx.ConnectError as error:
                    if attempt == attempts:
                        raise ModelError("unreachable", f"{self.role.role} model host unreachable") from error
                except httpx.TimeoutException as error:
                    raise ModelError("timeout", f"{self.role.role} model call timed out") from error
        if response.status_code >= 400:
            raise ModelError(
                "provider_error",
                f"{self.role.role} model returned HTTP {response.status_code}",
                status_code=response.status_code,
            )
        return response

    def _read_reply(self, response: httpx.Response, estimated: int, wall_ms: int) -> ModelReply:
        payload = response.json()
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        if choice.get("finish_reason") == "length":
            raise ModelError("output_limit", f"{self.role.role} model reply was cut off at max_tokens")
        usage = payload.get("usage") or {}
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
        return ModelReply(
            content=message.get("content") or "",
            tool_calls=message.get("tool_calls") or [],
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            cached_tokens=cached,
            estimated_prompt_tokens=estimated,
            wall_ms=wall_ms,
        )
