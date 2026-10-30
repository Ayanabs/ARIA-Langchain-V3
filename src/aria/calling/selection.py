"""Step 1 and the language half of step 4 in one constrained model call.

The model sees the question and the shortlist and returns: whether tools are needed, the goal tool,
and the arguments it can take from the user's words. Enumerations built from the shortlist make an
unknown tool or parameter impossible to express. Code then checks every argument: key values must
appear in the prompt (or be the caller's own), everything else must match the declared type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aria.calling.provenance import KeyValue, RejectedKey, accept_supplied_keys
from aria.calling.requests import ArgumentError, coerce_key_value
from aria.catalog.catalog import ToolCatalog
from aria.catalog.validation import CatalogTool
from aria.models.client import ChatModel, ModelReply

NO_TOOL = "none"


@dataclass
class ToolSelection:
    route: str
    goal: str | None
    # Tool -> non-key arguments taken from the user's words.
    arguments: dict[str, dict[str, Any]] = field(default_factory=dict)
    supplied_keys: dict[str, KeyValue] = field(default_factory=dict)
    rejected: list[str] = field(default_factory=list)
    reply: ModelReply | None = None


def selection_schema(tools: list[CatalogTool]) -> dict:
    arguments = {
        tool.name: {
            "type": "object",
            "properties": {
                parameter.name: {"type": parameter.type} for parameter in tool.declaration.parameters
            },
            "additionalProperties": False,
        }
        for tool in tools
    }
    return {
        "type": "object",
        "properties": {
            "route": {"type": "string", "enum": ["tools", "conversation"]},
            "goal_tool": {"type": "string", "enum": [tool.name for tool in tools] + [NO_TOOL]},
            "arguments": {"type": "object", "properties": arguments, "additionalProperties": False},
        },
        "required": ["route", "goal_tool", "arguments"],
        "additionalProperties": False,
    }


def describe_tools(tools: list[CatalogTool], catalog: ToolCatalog) -> str:
    lines = []
    for tool in tools:
        parameters = ", ".join(
            f"{parameter.name}: {parameter.type}{'' if parameter.required else ' (optional)'}"
            for parameter in tool.declaration.parameters
        )
        line = f"- {tool.name}({parameters}): {tool.description}"
        returned = _returned_fields(tool)
        if returned:
            line += f" Returns {returned}."
        for key_id in tool.required_keys:
            key = catalog.keys.get(key_id)
            producers = ", ".join(catalog.graph.producers_of(key_id)) or "none"
            line += f" Needs a {key.label}; found by: {producers}."
        lines.append(line)
    return "\n".join(lines)


# How many response fields to name per tool: enough to tell similar tools apart, few enough that the
# shortlist stays well inside the tool model's budget.
MAX_FIELDS_SHOWN = 12


def _returned_fields(tool: CatalogTool) -> str:
    """What the tool returns, from the live contract, so descriptions never drift from it."""
    response = tool.operation.response
    if response is None or not response.fields:
        return ""
    top_level = [name for name in response.fields if "." not in name]
    shown = ", ".join(top_level[:MAX_FIELDS_SHOWN])
    if len(top_level) > MAX_FIELDS_SHOWN:
        shown += ", ..."
    return f"{'a list of records' if response.is_list else 'one record'} with {shown}"


async def select_tools(
    question: str,
    shortlist: list[str],
    catalog: ToolCatalog,
    model: ChatModel,
    instructions: str,
    today: str,
    caller_keys: dict[str, tuple] | None = None,
) -> ToolSelection:
    tools = [catalog.tools[name] for name in shortlist]
    # Fixed instructions first and the request-specific part last, so the provider can reuse the
    # cached prefix.
    request = f"Tools:\n{describe_tools(tools, catalog)}\n\nToday's date: {today}\nQuestion: {question}"
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": request},
    ]
    reply = await model.complete(messages, schema=selection_schema(tools), schema_name="tool_selection")
    decision = reply.json()
    goal = decision.get("goal_tool")
    if decision.get("route") != "tools" or goal not in catalog.tools:
        return ToolSelection(route="conversation", goal=None, reply=reply)

    selection = ToolSelection(route="tools", goal=goal, reply=reply)
    proposed_keys: dict[str, tuple] = {}
    for tool_name, raw_arguments in (decision.get("arguments") or {}).items():
        if tool_name not in catalog.tools or not isinstance(raw_arguments, dict):
            continue
        tool = catalog.tools[tool_name]
        plain, keys = _split_arguments(tool, raw_arguments, selection.rejected)
        if plain:
            selection.arguments[tool_name] = plain
        proposed_keys.update(keys)
    accepted, rejected = accept_supplied_keys(proposed_keys, question, caller_keys)
    selection.supplied_keys = accepted
    selection.rejected += [_describe(item) for item in rejected]
    return selection


def _split_arguments(
    tool: CatalogTool, raw: dict, rejected: list[str]
) -> tuple[dict[str, Any], dict[str, tuple]]:
    """Separate plain arguments from key values, dropping any that fail the declared type."""
    plain: dict[str, Any] = {}
    for name, value in raw.items():
        parameter = tool.declaration.parameter(name)
        if parameter is None or value is None or name in tool.key_parameters:
            continue
        try:
            plain[name] = coerce_key_value(value, parameter.type)
        except ArgumentError as error:
            rejected.append(f"{tool.name}.{name}: {error}")

    keys = {}
    for key_id, parameters in tool.consumes.items():
        values = tuple(raw.get(name) for name in parameters)
        if all(value is not None for value in values):
            keys[key_id] = values
    return plain, keys


def _describe(item: RejectedKey) -> str:
    return f"{item.key_id}: {item.reason}"
