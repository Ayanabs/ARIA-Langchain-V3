"""Read the backend's OpenAPI document into the operations and response shapes tools bind to."""

from __future__ import annotations

from dataclasses import dataclass, field

from aria.catalog.config import OperationRef

HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head", "options")

# How deep nested response objects are flattened into dotted field paths. Keys sit near the top of
# a record; deeper nesting only grows the field list.
MAX_FIELD_DEPTH = 3


@dataclass(frozen=True)
class OperationParameter:
    name: str
    location: str
    required: bool
    type: str | None


@dataclass(frozen=True)
class ResponseShape:
    """The record shape an operation returns. `fields` maps dotted paths to JSON types."""

    is_list: bool
    fields: dict[str, str | None] = field(default_factory=dict)


@dataclass(frozen=True)
class Operation:
    operation_id: str | None
    method: str
    path: str
    summary: str
    description: str
    parameters: tuple[OperationParameter, ...]
    requires_body: bool
    response: ResponseShape | None

    @property
    def label(self) -> str:
        return f"{self.method.upper()} {self.path}"

    def parameter(self, name: str) -> OperationParameter | None:
        return next((parameter for parameter in self.parameters if parameter.name == name), None)


class OpenApiContract:
    def __init__(self, operations: list[Operation]):
        self.operations = operations

    @classmethod
    def from_document(cls, document: dict) -> OpenApiContract:
        components = document.get("components") or {}
        resolver = _SchemaResolver(components.get("schemas") or {}, components.get("parameters") or {})
        operations = []
        for path, path_item in (document.get("paths") or {}).items():
            shared_parameters = path_item.get("parameters", [])
            for method in HTTP_METHODS:
                spec = path_item.get(method)
                if spec is None:
                    continue
                operations.append(_read_operation(resolver, path, method, spec, shared_parameters))
        return cls(operations)

    def find(self, ref: OperationRef) -> tuple[Operation | None, str | None]:
        """Return the single operation the reference names, or a reason it names none or several."""
        if ref.id is not None:
            matches = [operation for operation in self.operations if operation.operation_id == ref.id]
            described = f"operationId {ref.id}"
        else:
            method = ref.method.lower()
            matches = [
                operation
                for operation in self.operations
                if operation.method == method and operation.path == ref.path
            ]
            described = f"{ref.method.upper()} {ref.path}"
        if not matches:
            return None, f"no backend operation matches {described}"
        if len(matches) > 1:
            return None, f"{described} matches {len(matches)} backend operations"
        return matches[0], None


def _read_operation(resolver, path: str, method: str, spec: dict, shared_parameters: list) -> Operation:
    # Operation-level parameters override path-level ones with the same name and location.
    by_identity = {}
    for raw in [*shared_parameters, *spec.get("parameters", [])]:
        raw = resolver.resolve_parameter(raw)
        by_identity[(raw.get("name"), raw.get("in"))] = raw
    parameters = tuple(
        OperationParameter(
            name=raw.get("name"),
            location=raw.get("in"),
            required=bool(raw.get("required")) or raw.get("in") == "path",
            type=resolver.json_type(raw.get("schema") or {}),
        )
        for raw in by_identity.values()
    )
    request_body = spec.get("requestBody") or {}
    return Operation(
        operation_id=spec.get("operationId"),
        method=method,
        path=path,
        summary=spec.get("summary") or "",
        description=spec.get("description") or "",
        parameters=parameters,
        requires_body=bool(request_body.get("required")),
        response=_read_response(resolver, spec.get("responses") or {}),
    )


def _read_response(resolver, responses: dict) -> ResponseShape | None:
    success = [code for code in responses if str(code).startswith("2")]
    if not success:
        return None
    content = responses[sorted(success)[0]].get("content") or {}
    if not content:
        return None
    media = content.get("application/json") or content.get("*/*") or next(iter(content.values()))
    schema = resolver.resolve(media.get("schema") or {})
    is_list = schema.get("type") == "array"
    if is_list:
        schema = resolver.resolve(schema.get("items") or {})
    fields: dict[str, str | None] = {}
    resolver.collect_fields(schema, prefix="", depth=1, fields=fields, seen=frozenset())
    return ResponseShape(is_list=is_list, fields=fields)


class _SchemaResolver:
    def __init__(self, schemas: dict, parameters: dict):
        self.schemas = schemas
        self.parameters = parameters

    def resolve(self, schema: dict) -> dict:
        seen = set()
        while "$ref" in schema:
            ref = schema["$ref"]
            if ref in seen:
                return {}
            seen.add(ref)
            schema = self.schemas.get(ref.rsplit("/", 1)[-1], {})
        if "allOf" in schema:
            merged = {"type": "object", "properties": {}}
            for part in schema["allOf"]:
                merged["properties"].update(self.resolve(part).get("properties", {}))
            return merged
        return schema

    def resolve_parameter(self, raw: dict) -> dict:
        if "$ref" in raw:
            return self.parameters.get(raw["$ref"].rsplit("/", 1)[-1], {})
        return raw

    def json_type(self, schema: dict) -> str | None:
        return self.resolve(schema).get("type")

    def collect_fields(self, schema: dict, *, prefix: str, depth: int, fields: dict, seen: frozenset) -> None:
        for name, raw_property in (schema.get("properties") or {}).items():
            path = f"{prefix}{name}"
            ref = raw_property.get("$ref")
            resolved = self.resolve(raw_property)
            fields[path] = resolved.get("type") or ("object" if resolved.get("properties") else None)
            nested = resolved.get("properties") and depth < MAX_FIELD_DEPTH and ref not in seen
            if nested:
                self.collect_fields(
                    resolved, prefix=f"{path}.", depth=depth + 1, fields=fields, seen=seen | {ref}
                )
