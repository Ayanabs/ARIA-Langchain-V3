"""The `@tool` decorator that tool modules use to declare a tool.

A tool module only declares: a typed function signature, a description of what the tool returns
and, optionally, parameter descriptions. It holds no endpoint paths, keys or organization values;
those come from the operation binding in deployment configuration. The function body is never
run: calls go to the bound backend operation.
"""

from __future__ import annotations

import datetime
import inspect
import types
import typing
from dataclasses import dataclass

# Marks decorated functions so the loader can find them; holds the ToolDeclaration.
DECLARATION_ATTRIBUTE = "__aria_tool__"

JSON_TYPES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    datetime.date: "string",
    datetime.datetime: "string",
}


class DeclarationError(Exception):
    """A tool function cannot be turned into a declaration."""


@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str
    required: bool
    description: str = ""


@dataclass(frozen=True)
class ToolDeclaration:
    name: str
    description: str
    parameters: tuple[ToolParameter, ...]
    module: str = ""

    def parameter(self, name: str) -> ToolParameter | None:
        return next((parameter for parameter in self.parameters if parameter.name == name), None)


def tool(function=None, *, name: str | None = None, description: str | None = None):
    """Declare a tool. Usable bare (`@tool`) or with arguments (`@tool(name=...)`).

    Parameter descriptions are given with `typing.Annotated[int, "what this is"]`.
    """

    def decorate(target):
        declaration = declaration_from_function(target, name=name, description=description)
        setattr(target, DECLARATION_ATTRIBUTE, declaration)
        return target

    if function is not None:
        return decorate(function)
    return decorate


def declaration_from_function(
    function, *, name: str | None = None, description: str | None = None
) -> ToolDeclaration:
    tool_name = name or function.__name__
    hints = typing.get_type_hints(function, include_extras=True)
    parameters = []
    for parameter in inspect.signature(function).parameters.values():
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            raise DeclarationError(f"{tool_name}: *args and **kwargs are not allowed")
        if parameter.name not in hints:
            raise DeclarationError(f"{tool_name}: parameter {parameter.name} has no type annotation")
        json_type, optional, parameter_description = _describe_annotation(tool_name, hints[parameter.name])
        has_default = parameter.default is not inspect.Parameter.empty
        parameters.append(
            ToolParameter(
                name=parameter.name,
                type=json_type,
                required=not (has_default or optional),
                description=parameter_description,
            )
        )
    return ToolDeclaration(
        name=tool_name,
        description=description or inspect.cleandoc(function.__doc__ or ""),
        parameters=tuple(parameters),
        module=function.__module__,
    )


def _describe_annotation(tool_name: str, annotation) -> tuple[str, bool, str]:
    """Return (JSON type, whether None is allowed, description) for one parameter annotation."""
    description = ""
    if typing.get_origin(annotation) is typing.Annotated:
        annotation, *metadata = typing.get_args(annotation)
        description = next((item for item in metadata if isinstance(item, str)), "")

    optional = False
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        members = [member for member in typing.get_args(annotation) if member is not type(None)]
        optional = len(members) < len(typing.get_args(annotation))
        if len(members) != 1:
            raise DeclarationError(f"{tool_name}: union parameter types are not supported")
        annotation = members[0]

    if annotation not in JSON_TYPES:
        raise DeclarationError(f"{tool_name}: unsupported parameter type {annotation!r}")
    return JSON_TYPES[annotation], optional, description
