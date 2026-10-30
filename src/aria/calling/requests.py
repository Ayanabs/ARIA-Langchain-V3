"""Turn tool arguments into a backend request, checking them against the tool's declaration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

from aria.catalog.validation import CatalogTool


class ArgumentError(ValueError):
    """Arguments do not match the tool's declared parameters."""


@dataclass(frozen=True)
class BackendRequest:
    method: str
    path: str
    query: dict[str, Any] = field(default_factory=dict)


def build_request(tool: CatalogTool, arguments: dict[str, Any]) -> BackendRequest:
    _check_arguments(tool, arguments)
    values = {tool.parameter_map[name]: value for name, value in arguments.items() if value is not None}
    values.update(tool.fixed)

    path = tool.operation.path
    query = {}
    for parameter in tool.operation.parameters:
        if parameter.name not in values:
            continue
        value = values[parameter.name]
        if parameter.location == "path":
            # safe="" encodes "/" too, so a value can never reach a different endpoint.
            path = path.replace("{" + parameter.name + "}", quote(_as_text(value), safe=""))
        elif parameter.location == "query":
            query[parameter.name] = _as_text(value)
    return BackendRequest(method=tool.operation.method.upper(), path=path, query=query)


def _check_arguments(tool: CatalogTool, arguments: dict[str, Any]) -> None:
    declared = {parameter.name: parameter for parameter in tool.declaration.parameters}
    unknown = sorted(set(arguments) - set(declared))
    if unknown:
        raise ArgumentError(f"{tool.name}: unknown arguments {', '.join(unknown)}")
    for parameter in declared.values():
        value = arguments.get(parameter.name)
        if value is None:
            if parameter.required:
                raise ArgumentError(f"{tool.name}: missing required argument {parameter.name}")
            continue
        if not _matches_type(value, parameter.type):
            raise ArgumentError(f"{tool.name}: {parameter.name} must be {parameter.type}")


def _matches_type(value: Any, json_type: str) -> bool:
    # bool is a subclass of int in Python, so it is excluded from the numeric types explicitly.
    if json_type == "boolean":
        return isinstance(value, bool)
    if isinstance(value, bool):
        return False
    if json_type == "integer":
        return isinstance(value, int)
    if json_type == "number":
        return isinstance(value, int | float)
    return isinstance(value, str)


def _as_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def coerce_key_value(value: Any, json_type: str) -> Any:
    """Convert a key value taken from a result or the prompt to the parameter's declared type.

    Only lossless conversions are made, such as "1042" to 1042 for an integer parameter; anything
    else raises ArgumentError rather than send a value the backend might match differently.
    """
    if json_type == "string":
        if isinstance(value, bool) or not isinstance(value, str | int):
            raise ArgumentError(f"cannot use {type(value).__name__} as a text key")
        return str(value)
    if json_type == "integer":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value.strip())
        raise ArgumentError("key value is not a whole number")
    if json_type == "number":
        if isinstance(value, int | float) and not isinstance(value, bool):
            return value
        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise ArgumentError("key value is not a number") from error
    if json_type == "boolean" and isinstance(value, bool):
        return value
    raise ArgumentError(f"cannot use {type(value).__name__} as a {json_type} key")
