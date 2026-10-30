"""Build the tool catalog from the registered tools, the backend contract and declared keys."""

from __future__ import annotations

import logging
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aria.catalog.config import CatalogConfig
from aria.catalog.graph import ChainPlan, KeyGraph
from aria.catalog.keys import KeySet, build_key_set
from aria.catalog.loader import LoadedTools, load_registered_tools
from aria.catalog.metadata import EntityMetadata
from aria.catalog.openapi import OpenApiContract
from aria.catalog.validation import CatalogTool, validate_tool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolCatalog:
    """One immutable catalog version. A reload builds a new one and swaps it in whole."""

    status: str  # "ready" or "failed"
    tools: dict[str, CatalogTool] = field(default_factory=dict)
    unavailable: dict[str, list[str]] = field(default_factory=dict)
    # Available tools with a required key that no tool produces; the user must supply it.
    missing_links: dict[str, list[str]] = field(default_factory=dict)
    keys: KeySet = field(default_factory=KeySet)
    graph: KeyGraph = field(default_factory=lambda: KeyGraph({}, max_depth=1))
    error: str | None = None
    built_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def plan(
        self,
        goal: str,
        supplied_keys: frozenset[str] | set[str] = frozenset(),
        filled: Mapping[str, Collection[str]] | None = None,
    ) -> ChainPlan:
        return self.graph.plan(goal, supplied_keys, filled)

    def diagnostics(self) -> dict:
        return {
            "status": self.status,
            "error": self.error,
            "built_at": self.built_at,
            "ready": sorted(self.tools),
            "unavailable": {name: reasons for name, reasons in sorted(self.unavailable.items())},
            "missing_links": {name: keys for name, keys in sorted(self.missing_links.items())},
            "keys": {
                key.id: {"entity": key.entity, "fields": list(key.fields), "source": key.source}
                for key in sorted(self.keys.keys.values(), key=lambda key: key.id)
            },
            "key_problems": self.keys.problems,
            "entities_without_declared_keys": self.keys.undeclared_entities,
            # Backend-inferred references: shown so they can be declared, never used to chain.
            "unconfirmed_reference_hints": self.keys.reference_hints,
        }


def failed_catalog(error: str) -> ToolCatalog:
    """A catalog with no tools, so a failed reload never leaves stale tools advertised as ready."""
    return ToolCatalog(status="failed", error=error)


def build_catalog(
    config: CatalogConfig,
    openapi_document: dict,
    metadata_document: dict,
    loaded: LoadedTools | None = None,
) -> ToolCatalog:
    loaded = loaded or load_registered_tools(config.tools_dir, config.modules)
    contract = OpenApiContract.from_document(openapi_document)
    key_set = build_key_set(EntityMetadata.from_document(metadata_document), config.keys)

    unavailable: dict[str, list[str]] = {name: list(reasons) for name, reasons in loaded.problems.items()}
    tools: dict[str, CatalogTool] = {}
    for name, declaration in loaded.declarations.items():
        tool, problems = validate_tool(declaration, config.tools.get(name), contract, key_set)
        if tool is None:
            unavailable[name] = problems
        else:
            tools[name] = tool
    for name in config.tools:
        if name not in loaded.declarations and name not in unavailable:
            unavailable[name] = ["binding in configuration has no registered tool"]

    tools, cycle_problems = _remove_cyclic_tools(tools, config.max_chain_depth)
    unavailable.update(cycle_problems)
    graph = KeyGraph(tools, config.max_chain_depth)
    catalog = ToolCatalog(
        status="ready",
        tools=tools,
        unavailable=unavailable,
        missing_links=_missing_links(graph),
        keys=key_set,
        graph=graph,
    )
    logger.info(
        "tool catalog built",
        extra={"tools_ready": len(tools), "tools_unavailable": len(unavailable)},
    )
    return catalog


def _remove_cyclic_tools(
    tools: dict[str, CatalogTool], max_depth: int
) -> tuple[dict[str, CatalogTool], dict[str, list[str]]]:
    """Drop tools that form a dependency loop: each needs a key only the next one can produce.

    Removing a tool can strand others that relied on it, so repeat until nothing changes.
    """
    problems: dict[str, list[str]] = {}
    while True:
        graph = KeyGraph(tools, max_depth)
        cyclic = {}
        for name in tools:
            plan = graph.plan(name)
            # Only the loop's members are removed. A tool that merely depends on the loop is planned
            # again next round, when it either finds another producer or reports a missing link.
            for member in plan.cycle:
                cyclic.setdefault(member, [f"dependency cycle: {' -> '.join(plan.cycle)}"])
        if not cyclic:
            return tools, problems
        problems.update(cyclic)
        tools = {name: tool for name, tool in tools.items() if name not in cyclic}


def _missing_links(graph: KeyGraph) -> dict[str, list[str]]:
    links = {}
    for name in graph.tools:
        plan = graph.plan(name)
        if plan.missing_keys:
            links[name] = list(plan.missing_keys)
    return links
