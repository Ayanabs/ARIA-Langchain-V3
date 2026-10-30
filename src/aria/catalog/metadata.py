"""Read Spring Boot's entity metadata (`/api/metadata/schema`).

The document maps entity -> field -> {kind, type}, where kind is "PK", "FK" or "field". "PK" comes
from the JPA `@Id`. "FK" is inferred by the backend from field names, so it is kept only as a hint and
never creates a link on its own.
"""

from __future__ import annotations

from dataclasses import dataclass

# Java types a single-column key can have. A PK of any other type is an `@EmbeddedId` class, whose
# parts the metadata does not list.
SCALAR_JAVA_TYPES = {
    "String", "Integer", "int", "Long", "long", "Short", "short", "Byte", "byte",
    "BigInteger", "BigDecimal", "Double", "double", "Float", "float", "Boolean", "boolean",
    "Character", "char", "UUID", "LocalDate", "LocalDateTime", "Date", "Instant",
}  # fmt: skip


@dataclass(frozen=True)
class Entity:
    name: str
    fields: dict[str, str]
    primary_key: tuple[str, ...]
    # True when the JPA key is an embedded class whose parts must be declared in configuration.
    embedded_primary_key: bool
    reference_hints: tuple[str, ...]


class EntityMetadata:
    def __init__(self, entities: dict[str, Entity]):
        self.entities = entities

    @classmethod
    def from_document(cls, document: dict) -> EntityMetadata:
        entities = {}
        for entity_name, raw_fields in document.items():
            if not isinstance(raw_fields, dict):
                continue
            fields = {}
            primary_key = []
            hints = []
            for field_name, info in raw_fields.items():
                info = info if isinstance(info, dict) else {}
                fields[field_name] = str(info.get("type") or "")
                if info.get("kind") == "PK":
                    primary_key.append(field_name)
                elif info.get("kind") == "FK":
                    hints.append(field_name)
            embedded = any(fields[name] not in SCALAR_JAVA_TYPES for name in primary_key)
            entities[entity_name] = Entity(
                name=entity_name,
                fields=fields,
                primary_key=() if embedded else tuple(primary_key),
                embedded_primary_key=embedded,
                reference_hints=tuple(hints),
            )
        return cls(entities)
