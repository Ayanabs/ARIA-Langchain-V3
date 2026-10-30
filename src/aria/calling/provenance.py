"""Where key values come from.

A key argument is valid only if its value came from an earlier result in the same request, from
the user's prompt, or from the caller's own identity. Values a model proposes are checked here
before a chain may use them; anything else is rejected with the reason.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

PROMPT = "prompt"
CALLER = "caller"


def result_source(tool_name: str) -> str:
    return f"result:{tool_name}"


@dataclass(frozen=True)
class KeyValue:
    key_id: str
    # One value per key field, in the key's field order.
    values: tuple[Any, ...]
    source: str


@dataclass(frozen=True)
class RejectedKey:
    key_id: str
    reason: str


def accept_supplied_keys(
    proposed: Mapping[str, tuple[Any, ...]],
    prompt: str,
    caller_keys: Mapping[str, tuple[Any, ...]] | None = None,
) -> tuple[dict[str, KeyValue], list[RejectedKey]]:
    """Keep proposed key values that appear in the prompt or are the caller's own; reject the rest."""
    caller_keys = caller_keys or {}
    accepted: dict[str, KeyValue] = {}
    rejected: list[RejectedKey] = []
    for key_id, values in proposed.items():
        values = tuple(values)
        if key_id in caller_keys and _same_values(values, tuple(caller_keys[key_id])):
            accepted[key_id] = KeyValue(key_id, values, CALLER)
            continue
        absent = [value for value in values if not _appears_in(value, prompt)]
        if absent:
            shown = ", ".join(repr(str(value)) for value in absent)
            rejected.append(
                RejectedKey(
                    key_id, f"{shown} is not in the prompt, an earlier result or the caller's identity"
                )
            )
            continue
        accepted[key_id] = KeyValue(key_id, values, PROMPT)
    return accepted, rejected


def _appears_in(value: Any, prompt: str) -> bool:
    text = str(value).strip()
    if not text:
        return False
    # Whole-token match, so 12 is not accepted because the prompt mentions 2012.
    pattern = r"(?<!\w)" + re.escape(text) + r"(?!\w)"
    return re.search(pattern, prompt, flags=re.IGNORECASE) is not None


def _same_values(left: tuple, right: tuple) -> bool:
    return len(left) == len(right) and all(str(a) == str(b) for a, b in zip(left, right, strict=True))
