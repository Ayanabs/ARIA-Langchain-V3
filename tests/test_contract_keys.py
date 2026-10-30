"""Keys declared by the backend contract itself (`x-aria-key`), with no ARIA key configuration."""

import copy

from aria.catalog.catalog import build_catalog
from tests.catalog_fixtures import METADATA, bindings_with, catalog_config, openapi_document


def marked_document(person_marker="staff_number", visit_marker="staff_number"):
    """The fake contract with the staff number marked on unitPeople's response and staffVisits' input."""
    document = copy.deepcopy(openapi_document())
    document["components"]["schemas"]["PersonDto"]["properties"]["staffNo"]["x-aria-key"] = person_marker
    visits = document["paths"]["/people/{staffNo}/visits"]["get"]
    visits["parameters"][0]["x-aria-key"] = visit_marker
    return document


def unmarked_bindings(tools_dir):
    """Bindings with the staff-number links removed, so only the contract can supply them."""
    tools = bindings_with(tools_dir)
    del tools["unitPeople"]["produces"]
    del tools["staffVisits"]["consumes"]
    return tools


def test_contract_markers_alone_link_tools_into_a_chain(tools_dir):
    config = catalog_config(tools_dir, tools=unmarked_bindings(tools_dir))

    catalog = build_catalog(config, marked_document(), METADATA)

    assert catalog.tools["staffVisits"].consumes == {"staff_number": ("staffNo",)}
    assert catalog.tools["unitPeople"].produces == {"staff_number": ("staffNo",)}
    assert [step.tool for step in catalog.plan("staffVisits").steps] == [
        "findUnits",
        "unitPeople",
        "staffVisits",
    ]


def test_without_markers_or_configuration_tools_do_not_chain(tools_dir):
    config = catalog_config(tools_dir, tools=unmarked_bindings(tools_dir))

    catalog = build_catalog(config, openapi_document(), METADATA)

    assert catalog.tools["staffVisits"].required_keys == ()
    assert catalog.graph.producers_of("staff_number") == []


def test_configuration_takes_precedence_over_the_contract(tools_dir):
    tools = bindings_with(tools_dir)
    tools["staffVisits"]["consumes"] = {"Ledger.staffNo": ["staffNo"]}
    config = catalog_config(tools_dir, tools=tools)

    catalog = build_catalog(config, marked_document(visit_marker="staff_number"), METADATA)

    # Both keys apply: the contract's marker and the configured one, which wins only for its own key.
    assert catalog.tools["staffVisits"].consumes == {
        "staff_number": ("staffNo",),
        "Ledger.staffNo": ("staffNo",),
    }


def test_marker_naming_an_undeclared_key_keeps_the_tool_unavailable(tools_dir):
    config = catalog_config(tools_dir, tools=unmarked_bindings(tools_dir))

    catalog = build_catalog(config, marked_document(visit_marker="no_such_key"), METADATA)

    assert "staffVisits" not in catalog.tools
    assert catalog.unavailable["staffVisits"] == ["key no_such_key is not declared (missing link)"]


def test_marked_fields_of_nested_records_do_not_produce_keys(tools_dir):
    document = marked_document()
    # UnitDto is nested inside PersonDto as a related record; its marker must not make unitPeople a
    # producer, and must not make the top-level marker ambiguous.
    document["components"]["schemas"]["UnitDto"]["properties"]["code"]["x-aria-key"] = "staff_number"
    config = catalog_config(tools_dir, tools=unmarked_bindings(tools_dir))

    catalog = build_catalog(config, document, METADATA)

    assert catalog.tools["unitPeople"].produces == {"staff_number": ("staffNo",)}
    # findUnits returns UnitDto at the top level, so there the marker does apply.
    assert "staff_number" in catalog.tools["findUnits"].produces
