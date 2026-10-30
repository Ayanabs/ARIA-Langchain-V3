"""Render model instructions from their templates.

Templates name deployment values as `{placeholder}`. Every placeholder must have a value, so a typo
in a template fails loudly instead of reaching the model as literal braces.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, model_validator

PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


class PromptError(ValueError):
    pass


def placeholders(template: str) -> set[str]:
    return set(PLACEHOLDER.findall(template))


def render(template: str, values: dict[str, str]) -> str:
    missing = placeholders(template) - set(values)
    if missing:
        raise PromptError(f"prompt has no value for {', '.join(sorted(missing))}")
    return PLACEHOLDER.sub(lambda match: values[match.group(1)], template)


class PromptsConfig(BaseModel):
    """Model instructions. Served locally until the prompts database is reachable.

    Templates may use `{placeholder}` for any name in `values`; rendering fails on unknown names.
    """

    model_config = ConfigDict(extra="forbid")

    values: dict[str, str] = {}
    tool_selection: str = ""
    synthesis: str = ""
    conversation: str = ""

    @model_validator(mode="after")
    def _placeholders_have_values(self) -> PromptsConfig:
        for name in ("tool_selection", "synthesis", "conversation"):
            unknown = placeholders(getattr(self, name)) - set(self.values)
            if unknown:
                raise ValueError(f"{name} uses undefined placeholders: {', '.join(sorted(unknown))}")
        return self

    def rendered(self, name: str) -> str:
        return render(getattr(self, name), self.values)
