"""Keys the backend contract marks on parameters and response fields (`x-aria-key`).

These are the backend's own declarations of which values identify records, so they link tools
without any ARIA configuration. They are merged with the bindings in configuration, which take
precedence for any key both name. Markers are read literally: nothing is inferred from names.
"""

from __future__ import annotations

from aria.catalog.openapi import Operation


def consumed_keys(operation: Operation, parameter_map: dict[str, str]) -> dict[str, list[str]]:
    """Key ID -> the tool parameters whose operation parameters the contract marks with that key."""
    tool_parameter_for = {operation_name: tool_name for tool_name, operation_name in parameter_map.items()}
    consumed: dict[str, list[str]] = {}
    for parameter in operation.parameters:
        if parameter.key and parameter.name in tool_parameter_for:
            consumed.setdefault(parameter.key, []).append(tool_parameter_for[parameter.name])
    return consumed


def produced_keys(operation: Operation) -> dict[str, list[str]]:
    """Key ID -> top-level response fields the contract marks with that key.

    Only top-level fields identify the records a tool returns. A marked field inside a nested object
    (a division's head, say) belongs to a related record, so it never makes the tool a producer.
    """
    response = operation.response
    if response is None:
        return {}
    produced: dict[str, list[str]] = {}
    for path, key_id in response.key_fields.items():
        if "." not in path:
            produced.setdefault(key_id, []).append(path)
    return produced
