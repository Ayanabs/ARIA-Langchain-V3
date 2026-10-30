"""A small fake backend contract and fake tool modules for catalog and chaining tests.

The fake domain deliberately mirrors the shapes that make key chaining hard in the real backend:
- `Person` has a surrogate JPA key `id`, while other records refer to people by `staffNo`, a
  business key declared in configuration.
- `Ledger` uses `staffNo` itself as its JPA key.
- `Membership` has an embedded (composite) JPA key whose parts must be declared.
- `Unit.code` is a key with no "id" in its name.
- The backend marks `Person.unitCode` and `Visit.staffNo` as inferred foreign keys (hints only).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from aria.catalog.catalog import build_catalog
from aria.catalog.config import CatalogConfig

METADATA = {
    "Person": {
        "id": {"kind": "PK", "type": "Long"},
        "staffNo": {"kind": "field", "type": "Integer"},
        "fullName": {"kind": "field", "type": "String"},
        "unitCode": {"kind": "FK", "type": "Integer"},
    },
    "Unit": {
        "code": {"kind": "PK", "type": "Integer"},
        "title": {"kind": "field", "type": "String"},
    },
    "Visit": {
        "visitId": {"kind": "PK", "type": "Long"},
        "staffNo": {"kind": "FK", "type": "Integer"},
        "day": {"kind": "field", "type": "LocalDate"},
    },
    "Ledger": {
        "staffNo": {"kind": "PK", "type": "Integer"},
        "balance": {"kind": "field", "type": "BigDecimal"},
    },
    "Membership": {
        "id": {"kind": "PK", "type": "MembershipId"},
        "groupRef": {"kind": "field", "type": "String"},
        "seat": {"kind": "field", "type": "Integer"},
    },
}

SCHEMAS = {
    "UnitDto": {"type": "object", "properties": {"code": {"type": "integer"}, "title": {"type": "string"}}},
    "PersonDto": {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "format": "int64"},
            "staffNo": {"type": "integer"},
            "fullName": {"type": "string"},
            "unit": {"$ref": "#/components/schemas/UnitDto"},
        },
    },
    "VisitDto": {
        "type": "object",
        "properties": {
            "visitId": {"type": "integer"},
            "staffNo": {"type": "integer"},
            "day": {"type": "string"},
        },
    },
    "LedgerDto": {
        "type": "object",
        "properties": {"staffNo": {"type": "integer"}, "balance": {"type": "number"}},
    },
    "MembershipDto": {
        "type": "object",
        "properties": {
            "groupRef": {"type": "string"},
            "seat": {"type": "integer"},
            "holder": {"type": "string"},
        },
    },
}


def path_param(name: str, type_: str = "integer") -> dict:
    return {"name": name, "in": "path", "required": True, "schema": {"type": type_}}


def query_param(name: str, type_: str = "string", required: bool = False) -> dict:
    return {"name": name, "in": "query", "required": required, "schema": {"type": type_}}


def operation(operation_id: str, schema: str | None, *, list_of: bool = True, parameters=(), **extra) -> dict:
    spec = {"operationId": operation_id, "parameters": list(parameters), **extra}
    if schema is not None:
        ref = {"$ref": f"#/components/schemas/{schema}"}
        body = {"type": "array", "items": ref} if list_of else ref
        spec["responses"] = {"200": {"description": "OK", "content": {"*/*": {"schema": body}}}}
    return spec


def base_paths() -> dict:
    return {
        "/units/search": {
            "get": operation("searchUnits", "UnitDto", parameters=[query_param("title", required=True)])
        },
        "/units/{code}/people": {
            "get": operation("listUnitPeople", "PersonDto", parameters=[path_param("code")])
        },
        "/people/{staffNo}/visits": {
            "get": operation("listVisits", "VisitDto", parameters=[path_param("staffNo")])
        },
        "/ledgers/{staffNo}": {
            "get": operation("getLedger", "LedgerDto", list_of=False, parameters=[path_param("staffNo")])
        },
        "/memberships": {"get": operation("listMemberships", "MembershipDto")},
        "/memberships/{groupRef}/{seat}": {
            "get": operation(
                "getMembership",
                "MembershipDto",
                list_of=False,
                parameters=[path_param("groupRef", "string"), path_param("seat")],
            )
        },
        "/visits": {
            "get": operation(
                "visitsByUnit", "VisitDto", parameters=[query_param("unitCode", "integer", True)]
            )
        },
    }


def openapi_document(paths: dict | None = None) -> dict:
    return {
        "openapi": "3.0.1",
        "paths": base_paths() if paths is None else paths,
        "components": {"schemas": SCHEMAS},
    }


TOOL_MODULES = {
    "units": '''
        from aria.catalog import tool

        @tool
        def findUnits(title: str) -> list:
            """Units whose title matches the given text."""
    ''',
    "people": '''
        from typing import Annotated
        from aria.catalog import tool

        @tool
        def unitPeople(unitCode: Annotated[int, "code of the unit"]) -> list:
            """People who belong to one unit."""
    ''',
    "visits": '''
        from aria.catalog import tool

        @tool
        def staffVisits(staffNo: int) -> list:
            """Visits recorded for one member of staff."""

        @tool
        def unitVisits(unitCode: int) -> list:
            """Visits for everyone in a unit."""
    ''',
    "ledgers": '''
        from aria.catalog import tool

        @tool
        def staffLedger(staffNo: int) -> dict:
            """The ledger balance of one member of staff."""
    ''',
    "memberships": '''
        from aria.catalog import tool

        @tool
        def allMemberships() -> list:
            """Every membership with its group and seat."""

        @tool
        def membershipBySeat(groupRef: str, seat: int) -> dict:
            """One membership, identified by group and seat."""
    ''',
}


def write_tool_modules(tools_dir: Path, modules: dict[str, str] | None = None) -> None:
    tools_dir.mkdir(parents=True, exist_ok=True)
    for name, source in (TOOL_MODULES if modules is None else modules).items():
        (tools_dir / f"{name}.py").write_text(textwrap.dedent(source), encoding="utf-8")


def catalog_config(tools_dir: Path, **overrides) -> CatalogConfig:
    values = {
        "tools_dir": tools_dir,
        "modules": list(TOOL_MODULES),
        "keys": {
            "staff_number": {"entity": "Person", "fields": ["staffNo"], "label": "staff number"},
            "membership": {"entity": "Membership", "fields": ["groupRef", "seat"], "label": "group and seat"},
        },
        "tools": {
            "findUnits": {
                "operation": {"id": "searchUnits"},
                "produces": {"Unit.code": ["code"]},
            },
            "unitPeople": {
                "operation": {"method": "get", "path": "/units/{code}/people"},
                "parameters": {"unitCode": "code"},
                "consumes": {"Unit.code": ["unitCode"]},
                "produces": {"staff_number": ["staffNo"]},
            },
            "staffVisits": {
                "operation": {"id": "listVisits"},
                "consumes": {"staff_number": ["staffNo"]},
            },
            # No `consumes`: the backend's inferred foreign key must not link this to findUnits.
            "unitVisits": {"operation": {"id": "visitsByUnit"}},
            "staffLedger": {
                "operation": {"id": "getLedger"},
                "consumes": {"Ledger.staffNo": ["staffNo"]},
            },
            "allMemberships": {
                "operation": {"id": "listMemberships"},
                "produces": {"membership": ["groupRef", "seat"]},
            },
            "membershipBySeat": {
                "operation": {"id": "getMembership"},
                "consumes": {"membership": ["groupRef", "seat"]},
            },
        },
    }
    values.update(overrides)
    return CatalogConfig.model_validate(values)


def build(tools_dir, paths=None, metadata=None, **config_overrides):
    config = catalog_config(tools_dir, **config_overrides)
    return build_catalog(config, openapi_document(paths), metadata or METADATA)


def bindings_with(tools_dir, **changes):
    tools = catalog_config(tools_dir).model_dump()["tools"]
    tools.update(changes)
    return tools
