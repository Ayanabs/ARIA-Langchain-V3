"""Deployment configuration of the tool catalog: registered modules, declared keys, bindings."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperationRef(BaseModel):
    """Which backend operation a tool calls: by operationId, or by method and path.

    Method and path are accepted because springdoc derives operationIds from Java method names and
    suffixes repeats (`getByCode_3`), so an operationId can change when an unrelated controller does.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    method: str | None = None
    path: str | None = None

    @model_validator(mode="after")
    def _one_way_to_identify(self) -> OperationRef:
        by_id = self.id is not None
        by_route = self.method is not None or self.path is not None
        if by_id == by_route:
            raise ValueError("give either id, or both method and path")
        if by_route and (self.method is None or self.path is None):
            raise ValueError("method and path must be given together")
        return self


class KeyDeclaration(BaseModel):
    """A business key: the fields that identify an entity's records where users and other tables
    refer to them, when that differs from the JPA key."""

    model_config = ConfigDict(extra="forbid")

    entity: str
    fields: list[str] = Field(min_length=1)
    label: str


class ToolBinding(BaseModel):
    """How a registered tool maps onto its backend operation and onto declared keys.

    `consumes` and `produces` map a key ID to fields listed in the key's field order: tool parameters
    for `consumes`, response fields (dotted for nested objects) for `produces`.
    """

    model_config = ConfigDict(extra="forbid")

    operation: OperationRef
    parameters: dict[str, str] = {}
    fixed: dict[str, str | int | float | bool] = {}
    consumes: dict[str, list[str]] = {}
    produces: dict[str, list[str]] = {}


class CatalogConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tools_dir: Path = Path("tools")
    # Directory of per-module binding files, relative to the catalog file; merged into `tools`.
    bindings_dir: Path | None = None
    modules: list[str] = []
    # Longest producer chain resolved for one goal tool, counting the goal itself.
    max_chain_depth: int = Field(default=4, ge=1)
    # Most calls one chain step may fan out to when earlier steps selected several subjects.
    max_fan_out: int = Field(default=20, ge=1)
    keys: dict[str, KeyDeclaration] = {}
    tools: dict[str, ToolBinding] = {}
