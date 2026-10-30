"""Validate one registered tool against the backend contract and the key set.

Every check fails closed: a tool with any problem is unavailable and is listed with all of its
reasons, so a mistake surfaces in diagnostics instead of at request time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aria.catalog.config import ToolBinding
from aria.catalog.declaration import ToolDeclaration, ToolParameter
from aria.catalog.keys import KeySet
from aria.catalog.openapi import OpenApiContract, Operation, OperationParameter

# Tools only read. A write reached through a language model's choice is not safe to automate.
ALLOWED_METHODS = {"get"}
SUPPORTED_PARAMETER_LOCATIONS = {"path", "query"}

# Tool parameter type -> operation parameter types it can be sent as.
COMPATIBLE_TYPES = {
    "string": {"string"},
    "integer": {"integer", "number", "string"},
    "number": {"number", "string"},
    "boolean": {"boolean", "string"},
}


@dataclass(frozen=True)
class CatalogTool:
    """A validated tool: its declaration bound to one backend operation and to declared keys."""

    declaration: ToolDeclaration
    description: str
    operation: Operation
    # Tool parameter -> operation parameter.
    parameter_map: dict[str, str]
    # Operation parameter -> configured value.
    fixed: dict[str, Any]
    # Key ID -> tool parameters, in the key's field order.
    consumes: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # Key ID -> response fields, in the key's field order.
    produces: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.declaration.name

    @property
    def required_keys(self) -> tuple[str, ...]:
        """Consumed keys the tool cannot be called without, so a chain has to supply them."""
        return tuple(
            sorted(
                key_id
                for key_id, parameters in self.consumes.items()
                if all(self.declaration.parameter(name).required for name in parameters)
            )
        )

    @property
    def key_parameters(self) -> set[str]:
        return {name for parameters in self.consumes.values() for name in parameters}


def validate_tool(
    declaration: ToolDeclaration,
    binding: ToolBinding | None,
    contract: OpenApiContract,
    key_set: KeySet,
) -> tuple[CatalogTool | None, list[str]]:
    if binding is None:
        return None, ["no operation binding in deployment configuration"]

    operation, problem = contract.find(binding.operation)
    if operation is None:
        return None, [problem]

    problems = []
    if operation.method not in ALLOWED_METHODS:
        problems.append(f"{operation.label} is not a read operation; only GET operations can be tools")
    if operation.requires_body:
        problems.append(f"{operation.label} requires a request body, which tools cannot send")

    description = declaration.description or operation.description or operation.summary
    if not description:
        problems.append("no description in the tool or the operation")

    parameter_map, mapping_problems = _map_parameters(declaration, binding, operation)
    problems += mapping_problems
    problems += _check_consumes(declaration, binding, key_set)
    problems += _check_produces(binding, operation, key_set)

    if problems:
        return None, problems
    return (
        CatalogTool(
            declaration=declaration,
            description=description,
            operation=operation,
            parameter_map=parameter_map,
            fixed=dict(binding.fixed),
            consumes={key_id: tuple(names) for key_id, names in binding.consumes.items()},
            produces={key_id: tuple(names) for key_id, names in binding.produces.items()},
        ),
        [],
    )


def _map_parameters(
    declaration: ToolDeclaration, binding: ToolBinding, operation: Operation
) -> tuple[dict[str, str], list[str]]:
    problems = []
    for name in binding.parameters:
        if declaration.parameter(name) is None:
            problems.append(f"parameter binding names {name}, which the tool does not declare")

    parameter_map: dict[str, str] = {}
    # Operation parameters some tool parameter is bound to, even if that binding is invalid; those
    # already have a reason, so they are not reported again as uncovered.
    bound_targets: set[str] = set()
    for tool_parameter in declaration.parameters:
        target_name = binding.parameters.get(tool_parameter.name, tool_parameter.name)
        target = operation.parameter(target_name)
        if target is not None:
            bound_targets.add(target_name)
        problem = _check_parameter_pair(tool_parameter, target_name, target, operation)
        if problem:
            problems.append(problem)
            continue
        if target_name in parameter_map.values():
            problems.append(f"operation parameter {target_name} is bound to more than one tool parameter")
            continue
        parameter_map[tool_parameter.name] = target_name

    for name in binding.fixed:
        target = operation.parameter(name)
        if target is None or target.location not in SUPPORTED_PARAMETER_LOCATIONS:
            problems.append(f"fixed value for {name}, which is not a path or query parameter")
        elif name in binding.parameters.values() or name in parameter_map.values():
            problems.append(f"operation parameter {name} has both a fixed value and a tool parameter")

    for target in operation.parameters:
        if not target.required:
            continue
        if target.location not in SUPPORTED_PARAMETER_LOCATIONS:
            problems.append(f"required {target.location} parameter {target.name} cannot be sent by tools")
        elif target.name in binding.fixed:
            continue
        elif target.name not in bound_targets:
            problems.append(f"required operation parameter {target.name} has no tool parameter")
        elif target.name in parameter_map.values():
            source = next(name for name, mapped in parameter_map.items() if mapped == target.name)
            if not declaration.parameter(source).required:
                problems.append(f"tool parameter {source} is optional but {target.name} is required")
    return parameter_map, problems


def _check_parameter_pair(
    tool_parameter: ToolParameter, target_name: str, target: OperationParameter | None, operation: Operation
) -> str | None:
    if target is None:
        return f"tool parameter {tool_parameter.name} has no operation parameter {target_name}"
    if target.location not in SUPPORTED_PARAMETER_LOCATIONS:
        return f"operation parameter {target_name} is a {target.location} parameter"
    if target.type is None:
        return f"operation parameter {target_name} has no declared type"
    if target.type not in COMPATIBLE_TYPES[tool_parameter.type]:
        return (
            f"tool parameter {tool_parameter.name} is {tool_parameter.type} "
            f"but {operation.label} expects {target.type} for {target_name}"
        )
    return None


def _check_consumes(declaration: ToolDeclaration, binding: ToolBinding, key_set: KeySet) -> list[str]:
    problems = []
    for key_id, names in binding.consumes.items():
        key = key_set.get(key_id)
        if key is None:
            problems.append(_undeclared_key(key_id, key_set))
            continue
        if len(names) != len(key.fields):
            problems.append(
                f"key {key_id} has {len(key.fields)} fields but {len(names)} parameters consume it"
            )
        for name in names:
            if declaration.parameter(name) is None:
                problems.append(f"key {key_id} is consumed by {name}, which the tool does not declare")
    return problems


def _check_produces(binding: ToolBinding, operation: Operation, key_set: KeySet) -> list[str]:
    problems = []
    for key_id, response_fields in binding.produces.items():
        key = key_set.get(key_id)
        if key is None:
            problems.append(_undeclared_key(key_id, key_set))
            continue
        if len(response_fields) != len(key.fields):
            problems.append(
                f"key {key_id} has {len(key.fields)} fields "
                f"but {len(response_fields)} response fields produce it"
            )
        if operation.response is None:
            problems.append(f"{operation.label} declares no response shape, so it cannot produce {key_id}")
            continue
        for name in response_fields:
            if name not in operation.response.fields:
                problems.append(f"{operation.label} response has no field {name} for key {key_id}")
    return problems


def _undeclared_key(key_id: str, key_set: KeySet) -> str:
    if key_id in key_set.problems:
        return f"key {key_id} is declared but invalid: {'; '.join(key_set.problems[key_id])}"
    return f"key {key_id} is not declared (missing link)"
