"""Startup verification.

Checks configuration, each model host's context capacity and the backend's published contracts.
It reads only metadata (model descriptions, OpenAPI, entity metadata): it makes no model calls,
runs no operational reads and invents no sample subjects. Each probe is a single attempt with the
preflight timeout; a failure is reported, never retried silently.
"""

from __future__ import annotations

import asyncio
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import StrEnum

import httpx

from aria.settings import ModelRole, Settings

HTTP_METHODS = frozenset({"get", "put", "post", "delete", "patch", "head", "options", "trace"})

# Addresses later steps of the request flow depend on. Unset ones are reported, not fatal, so the
# service can start while a deployment is being completed.
OPTIONAL_SERVICE_FIELDS = (
    "embedding_api_base",
    "embedding_model_name",
    "rag_service_url",
    "redis_host",
    "chats_db_host",
    "prompts_db_host",
)


class CheckStatus(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    detail: str
    data: dict = field(default_factory=dict)


@dataclass
class PreflightReport:
    checks: list[CheckResult]
    duration_ms: int

    @property
    def status(self) -> CheckStatus:
        statuses = {check.status for check in self.checks}
        if CheckStatus.FAIL in statuses:
            return CheckStatus.FAIL
        if CheckStatus.WARN in statuses:
            return CheckStatus.WARN
        return CheckStatus.OK

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "durationMs": self.duration_ms,
            "checks": [asdict(check) for check in self.checks],
        }


def check_config(settings: Settings) -> CheckResult:
    problems = []
    for role in settings.models.values():
        if role.profile.provider == "ollama" and not role.native_api_base:
            problems.append(
                f"{role.role} model: no native API base configured, so the context length "
                "cannot be set per request"
            )

    urls = {"spring_boot_base_url": settings.env.spring_boot_base_url}
    urls.update({f"{role.role} model api_base": role.api_base for role in settings.models.values()})
    for label, url in urls.items():
        if not _is_http_url(url):
            problems.append(f"{label}: not an http(s) URL")

    if problems:
        return CheckResult("config", CheckStatus.FAIL, "; ".join(problems))

    unset = [name.upper() for name in OPTIONAL_SERVICE_FIELDS if not getattr(settings.env, name)]
    if unset:
        return CheckResult("config", CheckStatus.WARN, "optional services not configured", {"unset": unset})
    return CheckResult("config", CheckStatus.OK, "configuration loaded")


def _is_http_url(value: str) -> bool:
    try:
        url = httpx.URL(value)
    except httpx.InvalidURL:
        return False
    return url.scheme in {"http", "https"} and bool(url.host)


def _auth_headers(role: ModelRole) -> dict[str, str]:
    if role.api_key and role.api_key.get_secret_value():
        return {"Authorization": f"Bearer {role.api_key.get_secret_value()}"}
    return {}


def _model_max_context(model_info: dict) -> int | None:
    # Ollama prefixes model_info keys with the architecture, e.g. "<arch>.context_length".
    for key, value in model_info.items():
        if key.endswith(".context_length") and isinstance(value, int):
            return value
    return None


async def check_model_context(role: ModelRole, client: httpx.AsyncClient) -> CheckResult:
    if role.profile.provider == "llama_cpp":
        return await _check_llama_cpp_context(role, client)
    return await _check_ollama_context(role, client)


async def _check_llama_cpp_context(role: ModelRole, client: httpx.AsyncClient) -> CheckResult:
    name = f"model_context:{role.role}"
    wanted = role.profile.context_tokens
    api_base = role.api_base.rstrip("/")
    # llama-server serves `/props` beside the OpenAI-compatible `/v1` routes.
    server_root = api_base.removesuffix("/v1")
    headers = _auth_headers(role)
    try:
        models = await client.get(f"{api_base}/models", headers=headers)
        props = await client.get(f"{server_root}/props", headers=headers)
    except httpx.HTTPError as error:
        return CheckResult(name, CheckStatus.FAIL, f"model host unreachable ({type(error).__name__})")
    if models.status_code != 200:
        return CheckResult(name, CheckStatus.FAIL, f"model list returned HTTP {models.status_code}")
    served = {model.get("id") for model in models.json().get("data") or []}
    if role.name not in served:
        return CheckResult(name, CheckStatus.FAIL, "model is not served by the host")
    if props.status_code != 200:
        return CheckResult(name, CheckStatus.FAIL, f"server properties returned HTTP {props.status_code}")

    slot_context = (props.json().get("default_generation_settings") or {}).get("n_ctx")
    data = {"model": role.name, "requestedContext": wanted, "slotContext": slot_context}
    if not isinstance(slot_context, int):
        return CheckResult(name, CheckStatus.FAIL, "host does not report its per-request context", data)
    if slot_context < wanted:
        return CheckResult(
            name, CheckStatus.FAIL, "configured context exceeds the host's per-request context", data
        )
    return CheckResult(name, CheckStatus.OK, "configured context fits the host's per-request context", data)


async def _check_ollama_context(role: ModelRole, client: httpx.AsyncClient) -> CheckResult:
    name = f"model_context:{role.role}"
    wanted = role.profile.context_tokens
    if not role.native_api_base:
        return CheckResult(name, CheckStatus.FAIL, "native API base not configured")

    base = role.native_api_base.rstrip("/")
    headers = _auth_headers(role)
    try:
        show = await client.post(f"{base}/api/show", json={"model": role.name}, headers=headers)
    except httpx.HTTPError as error:
        return CheckResult(name, CheckStatus.FAIL, f"model host unreachable ({type(error).__name__})")
    if show.status_code == 404:
        return CheckResult(name, CheckStatus.FAIL, "model is not available on the host")
    if show.status_code != 200:
        return CheckResult(name, CheckStatus.FAIL, f"model description returned HTTP {show.status_code}")

    model_max = _model_max_context(show.json().get("model_info") or {})
    data = {"model": role.name, "requestedContext": wanted, "modelMaxContext": model_max}
    if model_max is None:
        return CheckResult(name, CheckStatus.FAIL, "model does not declare its context length", data)
    if model_max < wanted:
        return CheckResult(name, CheckStatus.FAIL, "configured context exceeds the model's maximum", data)

    loaded_context = await _loaded_context(base, role, client, headers)
    data["loadedContext"] = loaded_context
    if loaded_context is not None and loaded_context != wanted:
        # Ollama reloads a model whose requested context differs from the loaded one; that is
        # correct but slow, so it is surfaced rather than hidden.
        return CheckResult(
            name,
            CheckStatus.WARN,
            "host has the model loaded with a different context; requests will trigger a reload",
            data,
        )
    return CheckResult(name, CheckStatus.OK, "context length can be honoured", data)


async def _loaded_context(
    base: str, role: ModelRole, client: httpx.AsyncClient, headers: dict[str, str]
) -> int | None:
    try:
        response = await client.get(f"{base}/api/ps", headers=headers)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    for model in response.json().get("models") or []:
        if role.name in (model.get("name"), model.get("model")):
            return model.get("context_length")
    return None


def summarize_openapi(document: dict) -> dict:
    """Count operations and find missing or duplicated operationIds (tools bind to these)."""
    operation_ids: list[str] = []
    without_id = 0
    for path_item in (document.get("paths") or {}).values():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            if operation.get("operationId"):
                operation_ids.append(operation["operationId"])
            else:
                without_id += 1
    duplicates = sorted(op_id for op_id, count in Counter(operation_ids).items() if count > 1)
    return {
        "openapiVersion": document.get("openapi"),
        "operations": len(operation_ids) + without_id,
        "operationsWithoutId": without_id,
        "duplicateOperationIds": duplicates,
    }


async def check_backend_openapi(settings: Settings, client: httpx.AsyncClient) -> CheckResult:
    name = "backend_openapi"
    url = settings.env.spring_boot_base_url.rstrip("/") + settings.deployment.backend.openapi_path
    try:
        response = await client.get(url, headers=settings.contract_headers())
    except httpx.HTTPError as error:
        return CheckResult(name, CheckStatus.FAIL, f"backend unreachable ({type(error).__name__})")
    if response.status_code != 200:
        return CheckResult(name, CheckStatus.FAIL, f"OpenAPI returned HTTP {response.status_code}")
    try:
        document = response.json()
    except ValueError:
        return CheckResult(name, CheckStatus.FAIL, "OpenAPI response is not JSON")
    if not isinstance(document, dict) or "openapi" not in document or "paths" not in document:
        return CheckResult(name, CheckStatus.FAIL, "response is not an OpenAPI document")

    summary = summarize_openapi(document)
    if summary["duplicateOperationIds"]:
        # Tools bound to a duplicated operationId are ambiguous; the catalog will keep them unavailable.
        return CheckResult(name, CheckStatus.WARN, "OpenAPI has duplicate operationIds", summary)
    return CheckResult(name, CheckStatus.OK, "OpenAPI loaded", summary)


async def check_backend_metadata(settings: Settings, client: httpx.AsyncClient) -> CheckResult:
    name = "backend_metadata"
    url = settings.env.spring_boot_base_url.rstrip("/") + settings.deployment.backend.metadata_schema_path
    try:
        response = await client.get(url, headers=settings.contract_headers())
    except httpx.HTTPError as error:
        return CheckResult(name, CheckStatus.FAIL, f"backend unreachable ({type(error).__name__})")
    if response.status_code != 200:
        return CheckResult(name, CheckStatus.FAIL, f"entity metadata returned HTTP {response.status_code}")
    try:
        response.json()
    except ValueError:
        return CheckResult(name, CheckStatus.FAIL, "entity metadata response is not JSON")
    return CheckResult(name, CheckStatus.OK, "entity metadata loaded")


async def run_preflight(
    settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> PreflightReport:
    """Run every check concurrently. `transport` lets tests substitute the network."""
    started = time.perf_counter()
    checks = [check_config(settings)]
    timeout = httpx.Timeout(settings.deployment.preflight.timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        probes = [check_model_context(role, client) for role in settings.models.values()]
        probes.append(check_backend_openapi(settings, client))
        probes.append(check_backend_metadata(settings, client))
        checks.extend(await asyncio.gather(*probes))
    duration_ms = round((time.perf_counter() - started) * 1000)
    return PreflightReport(checks=checks, duration_ms=duration_ms)
