"""The key graph and chain planning.

A tool that requires a key nobody supplied depends on the tools that produce that key, and those
may in turn require keys of their own: goal A needs a key from B, B needs a key from C. Planning
walks those declared links (and only those) back to tools that need nothing, and returns the calls
in the order they must run. Code runs the chain; no model is asked to work out the order.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field

from aria.catalog.validation import CatalogTool


@dataclass(frozen=True)
class ChainStep:
    tool: str
    # Key ID -> the earlier step's tool that produces it.
    key_sources: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ChainPlan:
    goal: str
    # Producers first; the goal tool is last.
    steps: tuple[ChainStep, ...]
    # Required keys that were neither supplied nor produced by any tool. Each is a missing link.
    missing_keys: tuple[str, ...] = ()
    # A dependency loop that blocked every producer of some key, as tool names.
    cycle: tuple[str, ...] = ()
    # The depth limit stopped planning before a producer chain reached a tool needing nothing.
    too_deep: bool = False

    @property
    def complete(self) -> bool:
        return not (self.missing_keys or self.cycle or self.too_deep)


class KeyGraph:
    def __init__(self, tools: Mapping[str, CatalogTool], max_depth: int):
        self.tools = dict(tools)
        self.max_depth = max_depth
        producers: dict[str, list[str]] = {}
        consumers: dict[str, list[str]] = {}
        for tool in self.tools.values():
            for key_id in tool.produces:
                producers.setdefault(key_id, []).append(tool.name)
            for key_id in tool.consumes:
                consumers.setdefault(key_id, []).append(tool.name)
        self.producers = {key_id: sorted(names) for key_id, names in producers.items()}
        self.consumers = {key_id: sorted(names) for key_id, names in consumers.items()}

    def producers_of(self, key_id: str) -> list[str]:
        return self.producers.get(key_id, [])

    def plan(
        self,
        goal: str,
        supplied_keys: frozenset[str] | set[str] = frozenset(),
        filled: Mapping[str, Collection[str]] | None = None,
    ) -> ChainPlan:
        """Plan the calls that obtain every key `goal` requires and the caller did not supply.

        `filled` names, per tool, the arguments the request supplies from the user's words. When
        given, a producer is usable only if all its required non-key arguments are filled, and
        producers the request supplied arguments for are preferred: asked about a person by name,
        the chain starts from the lookup given that name, not from some other tool that happens to
        produce the same key. Without it (catalog diagnostics), every argument counts as fillable.
        """
        if goal not in self.tools:
            raise KeyError(goal)
        result = _Planner(self, frozenset(supplied_keys), filled).resolve(goal, (goal,))
        return ChainPlan(
            goal=goal,
            steps=tuple(result.steps),
            missing_keys=tuple(sorted(result.missing)),
            cycle=result.cycle,
            too_deep=result.too_deep,
        )


class _Planner:
    """The state of planning one request, kept apart from the graph that requests share."""

    def __init__(
        self, graph: KeyGraph, supplied: frozenset[str], filled: Mapping[str, Collection[str]] | None
    ):
        self.graph = graph
        self.supplied = supplied
        self.filled = None if filled is None else {name: set(params) for name, params in filled.items()}

    def resolve(self, tool_name: str, path: tuple[str, ...]) -> _Resolution:
        tool = self.graph.tools[tool_name]
        resolution = _Resolution()
        key_sources: dict[str, str] = {}
        for key_id in tool.required_keys:
            if key_id in self.supplied:
                continue
            chosen = self._best_producer(key_id, tool_name, path)
            if chosen.producer is None:
                resolution.absorb_failure(key_id, chosen)
                continue
            resolution.add_steps(chosen.resolution.steps)
            key_sources[key_id] = chosen.producer
        resolution.add_steps([ChainStep(tool=tool_name, key_sources=key_sources)])
        return resolution

    def _best_producer(self, key_id: str, consumer: str, path: tuple[str, ...]) -> _Choice:
        # A tool that produces the key it consumes (a lookup by that key) cannot supply it to itself.
        candidates = [name for name in self.graph.producers_of(key_id) if name != consumer]
        choice = _Choice()
        if not candidates:
            choice.missing.add(key_id)
            return choice
        for candidate in sorted(candidates, key=self._preference):
            if not self._callable(candidate):
                choice.missing.add(key_id)
                continue
            if candidate in path:
                choice.cycle = choice.cycle or (*path[path.index(candidate) :], candidate)
                continue
            if len(path) >= self.graph.max_depth:
                choice.too_deep = True
                continue
            sub = self.resolve(candidate, (*path, candidate))
            if not sub.complete:
                choice.record_incomplete(sub)
                continue
            # Candidates arrive in preference order, so a later one wins only with a shorter chain
            # at the same preference; ties keep the earlier (alphabetical) one, deterministically.
            better = choice.producer is None or (
                self._preference(candidate)[0] == self._preference(choice.producer)[0]
                and len(sub.steps) < len(choice.resolution.steps)
            )
            if better:
                choice.producer = candidate
                choice.resolution = sub
        if choice.producer is not None:
            choice.missing.clear()
        return choice

    def _preference(self, tool_name: str) -> tuple[int, str]:
        targeted = self.filled is None or bool(self.filled.get(tool_name))
        return (0 if targeted else 1, tool_name)

    def _callable(self, tool_name: str) -> bool:
        """Whether the request supplies every required argument of the tool that is not a key."""
        if self.filled is None:
            return True
        tool = self.graph.tools[tool_name]
        filled = self.filled.get(tool_name, set())
        return all(
            parameter.name in filled
            for parameter in tool.declaration.parameters
            if parameter.required and parameter.name not in tool.key_parameters
        )


@dataclass
class _Resolution:
    steps: list[ChainStep] = field(default_factory=list)
    missing: set[str] = field(default_factory=set)
    cycle: tuple[str, ...] = ()
    too_deep: bool = False

    @property
    def complete(self) -> bool:
        return not (self.missing or self.cycle or self.too_deep)

    def add_steps(self, steps: list[ChainStep]) -> None:
        # One call per tool: a producer needed by two branches runs once.
        planned = {step.tool for step in self.steps}
        self.steps.extend(step for step in steps if step.tool not in planned)

    def absorb_failure(self, key_id: str, choice: _Choice) -> None:
        if choice.missing:
            self.missing |= choice.missing
        elif choice.cycle:
            self.cycle = self.cycle or choice.cycle
        elif choice.too_deep:
            self.too_deep = True
        else:
            self.missing.add(key_id)


@dataclass
class _Choice:
    producer: str | None = None
    resolution: _Resolution = field(default_factory=_Resolution)
    # Why rejected candidates failed, reported when no candidate succeeds. A missing key deeper in
    # the chain is reported in preference to a cycle, since supplying it is how the user unblocks it.
    missing: set[str] = field(default_factory=set)
    cycle: tuple[str, ...] = ()
    too_deep: bool = False

    def record_incomplete(self, sub: _Resolution) -> None:
        self.missing |= sub.missing
        self.cycle = self.cycle or sub.cycle
        self.too_deep = self.too_deep or sub.too_deep
