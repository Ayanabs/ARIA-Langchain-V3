"""Registration and validation of tools against the backend contract."""

import copy

import pytest

from aria.catalog.declaration import DeclarationError, declaration_from_function
from tests.catalog_fixtures import (
    bindings_with,
    build,
    catalog_config,
    openapi_document,
    operation,
    path_param,
    write_tool_modules,
)


def test_all_fake_tools_validate(tools_dir):
    catalog = build(tools_dir)

    assert catalog.status == "ready"
    assert catalog.unavailable == {}
    assert sorted(catalog.tools) == [
        "allMemberships", "findUnits", "membershipBySeat", "staffLedger",
        "staffVisits", "unitPeople", "unitVisits",
    ]  # fmt: skip


def test_tool_description_and_parameters_come_from_the_module(tools_dir):
    tool = build(tools_dir).tools["unitPeople"]

    assert tool.description == "People who belong to one unit."
    assert tool.declaration.parameter("unitCode").description == "code of the unit"
    assert tool.parameter_map == {"unitCode": "code"}


def test_unregistered_module_is_not_a_tool(tools_dir):
    write_tool_modules(
        tools_dir,
        {
            "stray": '''
                from aria.catalog import tool

                @tool
                def strayTool() -> list:
                    """Not registered."""
            '''
        },
    )
    tools = bindings_with(tools_dir, strayTool={"operation": {"id": "listMemberships"}})

    catalog = build(tools_dir, tools=tools)

    assert "strayTool" not in catalog.tools
    assert catalog.unavailable["strayTool"] == ["binding in configuration has no registered tool"]


def test_registered_tool_without_binding_is_unavailable(tools_dir):
    tools = bindings_with(tools_dir)
    del tools["unitVisits"]

    catalog = build(tools_dir, tools=tools)

    assert catalog.unavailable["unitVisits"] == ["no operation binding in deployment configuration"]


def test_broken_module_only_takes_down_its_own_tools(tools_dir):
    (tools_dir / "ledgers.py").write_text("raise RuntimeError('broken')\n", encoding="utf-8")

    catalog = build(tools_dir)

    assert catalog.unavailable["ledgers"][0].startswith("module failed to load: RuntimeError")
    assert "staffVisits" in catalog.tools


def test_same_tool_name_in_two_modules_is_ambiguous(tools_dir):
    write_tool_modules(tools_dir, {"copy": (tools_dir / "units.py").read_text()})
    modules = catalog_config(tools_dir).modules + ["copy"]

    catalog = build(tools_dir, modules=modules)

    assert "findUnits" not in catalog.tools
    assert "more than one registered module" in catalog.unavailable["findUnits"][0]


def test_adding_a_tool_needs_no_code_change(tools_dir):
    before = build(tools_dir)
    assert "unitTitle" not in before.tools

    # A new backend endpoint, a thin module and its binding: nothing else changes.
    write_tool_modules(
        tools_dir,
        {
            "unit_title": '''
                from aria.catalog import tool

                @tool
                def unitTitle(staffNo: int) -> list:
                    """Titles of the units a member of staff has visited."""
            '''
        },
    )
    paths = openapi_document()["paths"]
    paths["/people/{staffNo}/unit-titles"] = {
        "get": operation("listUnitTitles", "UnitDto", parameters=[path_param("staffNo")])
    }
    tools = bindings_with(
        tools_dir,
        unitTitle={"operation": {"id": "listUnitTitles"}, "consumes": {"staff_number": ["staffNo"]}},
    )
    modules = catalog_config(tools_dir).modules + ["unit_title"]

    after = build(tools_dir, paths=paths, modules=modules, tools=tools)

    assert "unitTitle" in after.tools
    assert [step.tool for step in after.plan("unitTitle").steps] == ["findUnits", "unitPeople", "unitTitle"]


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (
            {"operation": {"id": "noSuchOperation"}},
            "no backend operation matches operationId noSuchOperation",
        ),
        ({"operation": {"method": "get", "path": "/nowhere"}}, "no backend operation matches GET /nowhere"),
        ({"produces": {"Unit.code": ["unitNumber"]}}, "response has no field unitNumber for key Unit.code"),
        ({"produces": {"Region.code": ["code"]}}, "key Region.code is not declared (missing link)"),
        ({"parameters": {"title": "name"}}, "tool parameter title has no operation parameter name"),
    ],
)
def test_binding_problems_keep_the_tool_unavailable(tools_dir, change, expected):
    binding = catalog_config(tools_dir).model_dump()["tools"]["findUnits"]
    binding.update(change)

    catalog = build(tools_dir, tools=bindings_with(tools_dir, findUnits=binding))

    assert "findUnits" not in catalog.tools
    assert any(expected in reason for reason in catalog.unavailable["findUnits"])


def test_ambiguous_operation_id_is_rejected(tools_dir):
    paths = openapi_document()["paths"]
    paths["/units/search-again"] = {"get": copy.deepcopy(paths["/units/search"]["get"])}

    catalog = build(tools_dir, paths=paths)

    assert catalog.unavailable["findUnits"] == ["operationId searchUnits matches 2 backend operations"]


def test_write_operations_are_never_tools(tools_dir):
    paths = openapi_document()["paths"]
    paths["/units/search"] = {"post": paths["/units/search"]["get"]}
    binding = {"operation": {"method": "post", "path": "/units/search"}, "produces": {"Unit.code": ["code"]}}

    catalog = build(tools_dir, paths=paths, tools=bindings_with(tools_dir, findUnits=binding))

    assert any("not a read operation" in reason for reason in catalog.unavailable["findUnits"])


def test_incompatible_parameter_type_is_rejected(tools_dir):
    write_tool_modules(
        tools_dir,
        {
            "people": '''
                from aria.catalog import tool

                @tool
                def unitPeople(unitCode: str) -> list:
                    """People who belong to one unit."""
            '''
        },
    )

    catalog = build(tools_dir)

    assert catalog.unavailable["unitPeople"] == [
        "tool parameter unitCode is string but GET /units/{code}/people expects integer for code"
    ]


def test_required_operation_parameter_must_be_covered(tools_dir):
    write_tool_modules(
        tools_dir,
        {
            "units": '''
                from aria.catalog import tool

                @tool
                def findUnits() -> list:
                    """All units."""
            '''
        },
    )

    catalog = build(tools_dir)

    assert catalog.unavailable["findUnits"] == ["required operation parameter title has no tool parameter"]


def test_nested_response_fields_can_produce_keys(tools_dir):
    tools = bindings_with(tools_dir)
    tools["unitPeople"]["produces"] = {"staff_number": ["staffNo"], "Unit.code": ["unit.code"]}

    catalog = build(tools_dir, tools=tools)

    assert "Unit.code" in catalog.tools["unitPeople"].produces


def test_declaration_rejects_untyped_parameters():
    def untyped(value):
        """No annotation."""

    with pytest.raises(DeclarationError, match="no type annotation"):
        declaration_from_function(untyped)
