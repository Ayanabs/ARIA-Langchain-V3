"""Register explicit Python tools or tools generated from an API contract."""
import os
import asyncio
import time

TOOL_CATALOG_MODE = os.getenv("ARIA_TOOL_CATALOG_MODE", "openapi").strip().lower()
if TOOL_CATALOG_MODE not in {"legacy", "openapi", "python"}:
    raise ValueError("ARIA_TOOL_CATALOG_MODE must be 'python', 'legacy' or 'openapi'")
if TOOL_CATALOG_MODE in {"legacy", "python"}:
    from . import legacy_catalog
    for _k, _v in vars(legacy_catalog).items():
        if not _k.startswith("_"):
            globals()[_k] = _v
# Collect all static unique LangChain tool objects defined/imported in this package
_seen_tool_names = set()
all_tools = []
for obj in list(globals().values()):
    if hasattr(obj, "name") and hasattr(obj, "invoke") and hasattr(obj, "description"):
        if obj.name not in _seen_tool_names:
            _seen_tool_names.add(obj.name)
            all_tools.append(obj)

# O(1) Fast Function Pointer Tool Registry Map
TOOL_MAP = {t.name: t for t in all_tools}
_discovery_lock = None
_discovery_retry_after = 0.0


def register_dynamic_tools(new_tools: list) -> int:
    """Registers dynamically discovered OpenAPI tools in RAM."""
    global all_tools, TOOL_MAP
    if TOOL_CATALOG_MODE == "python":
        return 0
    added_count = 0
    for t in new_tools:
        if not hasattr(t, "name") or not hasattr(t, "invoke"):
            continue
        if t.name not in TOOL_MAP:
            all_tools.append(t)
            TOOL_MAP[t.name] = t
            added_count += 1
    return added_count


async def load_dynamic_tools(openapi_url: str = None) -> list:
    """Coalesce concurrent discovery and briefly back off failed contract loads."""
    global _discovery_lock, _discovery_retry_after
    if _discovery_lock is None:
        _discovery_lock = asyncio.Lock()
    if time.monotonic() < _discovery_retry_after:
        return get_all_tools()
    async with _discovery_lock:
        if time.monotonic() < _discovery_retry_after:
            return get_all_tools()
        result = await _load_dynamic_tools(openapi_url)
        if not result:
            _discovery_retry_after = time.monotonic() + 15.0
        return result


async def _load_dynamic_tools(openapi_url: str = None) -> list:
    """Dynamically loads and materializes OpenAPI 3.0 tools into the registry in memory if enabled."""
    import os
    import logging
    from aria_agent.config.config import DYNAMIC_TOOLS_ENABLED

    if TOOL_CATALOG_MODE == "python":
        from aria_agent.services.python_tool_contracts import enrich_python_tools
        try:
            await enrich_python_tools(all_tools, openapi_url)
        except Exception as error:
            for tool in all_tools:
                tool.metadata = {**(tool.metadata or {}), "contract_validation": {
                    "status": "unavailable", "issues": [{"code": "schema_load_failed"}], "execution": "not_checked"}}
            from aria_agent.services.query_failures import QueryFailure
            if isinstance(error, QueryFailure):
                raise
            status = getattr(getattr(error, "response", None), "status_code", None)
            raise QueryFailure("source_discovery_failed", "capability_selection", status_code=status) from error
        return get_all_tools()

    if not DYNAMIC_TOOLS_ENABLED and TOOL_CATALOG_MODE != "openapi":
        return all_tools

    from aria_agent.services.openapi_loader import build_tools_from_openapi

    from aria_agent.config.config import API_CONFIG
    spec_url = openapi_url or os.getenv("OPENAPI_SPEC_URL") or API_CONFIG.get("spec_url")
    from aria_agent.services.query_failures import QueryFailure
    if not spec_url or not str(spec_url).strip():
        raise QueryFailure("source_configuration_missing", "capability_selection")
    try:
        discovered_tools = await build_tools_from_openapi(spec_url)
        if TOOL_CATALOG_MODE == "openapi":
            # An empty successful contract also revokes every old operation.
            all_tools.clear()
            TOOL_MAP.clear()
        if discovered_tools:
            added = register_dynamic_tools(discovered_tools)
            logging.getLogger("langchain-agent").info(
                f"[ToolRegistry] Dynamically registered {added} tools from OpenAPI ({len(all_tools)} total tools active)."
            )
    except Exception as error:
        logging.getLogger("langchain-agent").warning("[ToolRegistry] API contract loading failed (%s)", type(error).__name__)
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        raise QueryFailure("source_discovery_failed", "capability_selection", status_code=status_code) from error

    return all_tools


def get_all_tools() -> list:
    """Return usable planning capabilities, excluding unverified Python readers."""
    if TOOL_CATALOG_MODE == "python":
        return [tool for tool in all_tools if ((tool.metadata or {}).get("contract_validation") or {}).get("status") == "ready"]
    return list(all_tools)


def get_registered_tools() -> list:
    """Include unavailable readers for diagnosis and offline inventory audits."""
    return list(all_tools)


def catalog_validation_report() -> list:
    """Return structural results, never caller data or schema service credentials."""
    return [{"name": tool.name, **((tool.metadata or {}).get("contract_validation") or {
        "status": "pending", "issues": [], "execution": "not_checked"})} for tool in all_tools]


def catalog_readiness() -> dict:
    """Report readiness without exposing deployment URLs or credentials."""
    from aria_agent.config.config import API_CONFIG
    configured = bool((os.getenv("OPENAPI_SPEC_URL") or API_CONFIG.get("spec_url") or "").strip())
    if TOOL_CATALOG_MODE == "openapi" and not configured:
        return {"status": "not_ready", "reason": "source_configuration_missing", "toolCount": 0}
    if not all_tools:
        return {"status": "not_ready", "reason": "source_catalog_unavailable", "toolCount": 0}
    if TOOL_CATALOG_MODE == "python":
        from aria_agent.config.config import AGENT_MANIFEST, IDENTITY_CONFIG
        bindings = AGENT_MANIFEST.get("python_tool_contracts") or {}
        active = {tool.name for tool in get_all_tools()}
        counts = {"toolCount": len(active), "registeredToolCount": len(all_tools),
                  "unavailableToolCount": len(all_tools) - len(active)}
        if any(name not in active for name in bindings):
            return {"status": "not_ready", "reason": "python_tool_contracts_unavailable", **counts}
        lookup = IDENTITY_CONFIG.get("name_lookup_operation")
        if lookup and lookup not in active:
            return {"status": "not_ready", "reason": "identity_lookup_unavailable", **counts}
        if not active:
            return {"status": "not_ready", "reason": "python_tool_contracts_unavailable", **counts}
        return {"status": "ready", **counts}
    return {"status": "ready", "toolCount": len(all_tools)}

