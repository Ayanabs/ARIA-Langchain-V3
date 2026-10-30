"""The key set: every field combination that identifies records, built only from declarations.

Two of the four declared sources define keys: JPA primary keys from the entity metadata and
business keys from deployment configuration. The other two (tool parameter and response bindings)
say which tools consume and produce those keys; see `graph.py`. Foreign-key hints from the metadata
are listed for diagnostics only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aria.catalog.config import KeyDeclaration
from aria.catalog.metadata import EntityMetadata


@dataclass(frozen=True)
class Key:
    id: str
    entity: str
    fields: tuple[str, ...]
    label: str
    source: str  # "jpa" or "business"


@dataclass
class KeySet:
    keys: dict[str, Key] = field(default_factory=dict)
    problems: dict[str, list[str]] = field(default_factory=dict)
    # Entities whose JPA key is embedded and has no business key declared, so none of their keys
    # can be chained.
    undeclared_entities: list[str] = field(default_factory=list)
    reference_hints: list[str] = field(default_factory=list)

    def get(self, key_id: str) -> Key | None:
        return self.keys.get(key_id)


def jpa_key_id(entity: str, fields: tuple[str, ...]) -> str:
    return f"{entity}.{'+'.join(fields)}"


def build_key_set(metadata: EntityMetadata, declared: dict[str, KeyDeclaration]) -> KeySet:
    key_set = KeySet()
    for entity in metadata.entities.values():
        if entity.primary_key:
            key_id = jpa_key_id(entity.name, entity.primary_key)
            key_set.keys[key_id] = Key(
                id=key_id,
                entity=entity.name,
                fields=entity.primary_key,
                label=f"{entity.name} {', '.join(entity.primary_key)}",
                source="jpa",
            )
        key_set.reference_hints.extend(f"{entity.name}.{hint}" for hint in entity.reference_hints)

    for key_id, declaration in declared.items():
        problems = _check_declaration(metadata, declaration)
        if problems:
            key_set.problems[key_id] = problems
            continue
        if key_id in key_set.keys:
            key_set.problems[key_id] = ["key ID is already used by a JPA primary key"]
            continue
        key_set.keys[key_id] = Key(
            id=key_id,
            entity=declaration.entity,
            fields=tuple(declaration.fields),
            label=declaration.label,
            source="business",
        )

    entities_with_keys = {key.entity for key in key_set.keys.values()}
    key_set.undeclared_entities = sorted(
        entity.name
        for entity in metadata.entities.values()
        if entity.embedded_primary_key and entity.name not in entities_with_keys
    )
    return key_set


def _check_declaration(metadata: EntityMetadata, declaration: KeyDeclaration) -> list[str]:
    entity = metadata.entities.get(declaration.entity)
    if entity is None:
        return [f"entity {declaration.entity} is not in the backend's entity metadata"]
    missing = [name for name in declaration.fields if name not in entity.fields]
    if missing:
        return [f"entity {declaration.entity} has no field {name}" for name in missing]
    if len(set(declaration.fields)) != len(declaration.fields):
        return ["a key field is listed twice"]
    return []
