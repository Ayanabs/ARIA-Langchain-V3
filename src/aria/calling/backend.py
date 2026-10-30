"""Call backend operations over HTTP on behalf of the user."""

from __future__ import annotations

from typing import Any

import httpx

from aria.calling.requests import BackendRequest
from aria.catalog.validation import CatalogTool
from aria.settings import Settings


class BackendCallError(Exception):
    """A backend operation failed. Carries the status code when there was a response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BackendInvoker:
    """Sends tool requests to the backend with the caller's own credentials.

    Only connection failures are retried, up to the configured budget. A request the backend has
    received is not retried, so a slow backend is not hit twice for one call.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        authorization: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        http = settings.deployment.http
        self.base_url = settings.env.spring_boot_base_url.rstrip("/")
        self.retries = http.retries
        self.timeout = httpx.Timeout(http.read_timeout_seconds, connect=http.connect_timeout_seconds)
        # Passed through unchanged: the backend checks the caller's token and authorization.
        self.headers = {"Authorization": authorization} if authorization else {}
        self.transport = transport

    async def __call__(self, tool: CatalogTool, request: BackendRequest) -> Any:
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            response = await self._send(client, request, tool.operation.label)
        if response.status_code >= 400:
            raise BackendCallError(
                f"{request.method} {tool.operation.path} returned {response.status_code}",
                status_code=response.status_code,
            )
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise BackendCallError(f"{request.method} {tool.operation.path} did not return JSON") from error

    async def _send(self, client: httpx.AsyncClient, request: BackendRequest, label: str) -> httpx.Response:
        # Messages name the operation template, not the filled path, so key values stay out of logs.
        attempts = self.retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return await client.request(
                    request.method,
                    self.base_url + request.path,
                    params=request.query,
                    headers=self.headers,
                )
            except httpx.ConnectError as error:
                if attempt == attempts:
                    raise BackendCallError(
                        f"{label}: backend unreachable after {attempts} attempts"
                    ) from error
            except httpx.TimeoutException as error:
                raise BackendCallError(f"{label} timed out") from error
        raise AssertionError("unreachable")
