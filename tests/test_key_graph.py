"""Keys from the four declared sources, and chain planning over them."""

import pytest

from tests.catalog_fixtures import (
    bindings_with,
    build,
    catalog_config,
    openapi_document,
    operation,
    query_param,
    write_tool_modules,
)


def test_three_step_chain_is_planned_in_dependency_order(tools_dir):
    catalog = build(tools_dir)

    plan = catalog.plan("staffVisits")

    assert plan.complete
    assert [step.tool for step in plan.steps] == ["findUnits", "unitPeople", "staffVisits"]
    assert plan.steps[1].key_sources == {"Unit.code": "findUnits"}
    assert plan.steps[2].key_sources == {"staff_number": "unitPeople"}


def test_a_supplied_key_shortens_the_chain(tools_dir):
    catalog = build(tools_dir)

    assert [step.tool for step in catalog.plan("staffVisits", {"Unit.code"}).steps] == [
        "unitPeople",
        "staffVisits",
    ]
    assert [step.tool for step in catalog.plan("staffVisits", {"staff_number"}).steps] == ["staffVisits"]


def test_business_key_differs_from_surrogate_jpa_key(tools_dir):
    catalog = build(tools_dir)

    assert catalog.keys.get("Person.id").source == "jpa"
    assert catalog.keys.get("staff_number").fields == ("staffNo",)
    # Chaining uses the declared business key; nothing produces or consumes the surrogate key.
    assert catalog.graph.producers_of("Person.id") == []
    assert catalog.graph.producers_of("staff_number") == ["unitPeople"]


def test_entity_whose_jpa_key_is_the_business_key(tools_dir):
    catalog = build(tools_dir)

    assert catalog.keys.get("Ledger.staffNo").source == "jpa"
    assert catalog.tools["staffLedger"].required_keys == ("Ledger.staffNo",)


def test_jpa_key_and_business_key_with_the_same_field_stay_distinct(tools_dir):
    # Ledger.staffNo and staff_number are both "staffNo", but no declaration links them, so a
    # staff number from unitPeople is not offered to staffLedger.
    plan = build(tools_dir).plan("staffLedger")

    assert not plan.complete
    assert plan.missing_keys == ("Ledger.staffNo",)


def test_composite_key_is_chained_through_all_of_its_fields(tools_dir):
    catalog = build(tools_dir)

    assert catalog.keys.get("membership").fields == ("groupRef", "seat")
    assert "Membership" not in catalog.keys.undeclared_entities
    plan = catalog.plan("membershipBySeat")
    assert [step.tool for step in plan.steps] == ["allMemberships", "membershipBySeat"]


def test_embedded_jpa_key_without_declaration_is_reported(tools_dir):
    config_keys = {"staff_number": {"entity": "Person", "fields": ["staffNo"], "label": "staff number"}}
    tools = bindings_with(tools_dir)
    del tools["allMemberships"]["produces"]
    del tools["membershipBySeat"]

    catalog = build(tools_dir, keys=config_keys, tools=tools)

    assert catalog.keys.undeclared_entities == ["Membership"]
    assert "membershipBySeat" in catalog.unavailable


def test_key_with_no_id_in_its_name(tools_dir):
    catalog = build(tools_dir)

    assert catalog.keys.get("Unit.code").fields == ("code",)
    assert catalog.graph.producers_of("Unit.code") == ["findUnits"]


def test_inferred_foreign_key_does_not_chain(tools_dir):
    catalog = build(tools_dir)

    # The backend marks Person.unitCode and Visit.staffNo as foreign keys, but they are only hints.
    assert "Person.unitCode" in catalog.diagnostics()["unconfirmed_reference_hints"]
    assert catalog.tools["unitVisits"].required_keys == ()
    assert [step.tool for step in catalog.plan("unitVisits").steps] == ["unitVisits"]
    assert "unitVisits" not in catalog.graph.consumers.get("Unit.code", [])


def test_business_key_on_unknown_field_is_rejected(tools_dir):
    keys = {"staff_number": {"entity": "Person", "fields": ["employeeNumber"], "label": "staff number"}}

    catalog = build(tools_dir, keys=keys)

    assert catalog.keys.problems["staff_number"] == ["entity Person has no field employeeNumber"]
    assert "staffVisits" in catalog.unavailable
    assert "unitPeople" in catalog.unavailable


def test_missing_producer_is_reported_as_a_missing_link(tools_dir):
    catalog = build(tools_dir)

    # Still callable when the user gives the key, so the tool stays available.
    assert "staffLedger" in catalog.tools
    assert catalog.missing_links == {"staffLedger": ["Ledger.staffNo"]}


def test_dependency_cycle_makes_tools_unavailable(tools_dir):
    write_tool_modules(
        tools_dir,
        {
            "loop": '''
                from aria.catalog import tool

                @tool
                def unitOfPerson(staffNo: int) -> list:
                    """The unit a member of staff belongs to."""
            '''
        },
    )
    tools = bindings_with(
        tools_dir,
        unitOfPerson={
            "operation": {"id": "listVisits"},
            "consumes": {"staff_number": ["staffNo"]},
            "produces": {"Unit.code": ["staffNo"]},
        },
    )
    # Without findUnits, Unit.code only comes from unitOfPerson, which needs a staff number,
    # which only comes from unitPeople, which needs Unit.code.
    del tools["findUnits"]
    modules = [name for name in catalog_config(tools_dir).modules if name != "units"] + ["loop"]

    catalog = build(tools_dir, modules=modules, tools=tools)

    assert catalog.unavailable["unitPeople"][0].startswith("dependency cycle: unitPeople -> unitOfPerson")
    assert "unitOfPerson" in catalog.unavailable
    assert "unitPeople" not in catalog.tools
    # With the loop removed nothing produces a staff number, so staffVisits needs it from the user.
    assert catalog.missing_links["staffVisits"] == ["staff_number"]


def test_chain_depth_is_bounded(tools_dir):
    catalog = build(tools_dir, max_chain_depth=2)

    plan = catalog.plan("staffVisits")

    assert plan.too_deep
    assert not plan.complete


@pytest.fixture
def two_staff_producers(tools_dir):
    """staff_number from either a name lookup (one step) or unit membership (two steps)."""
    write_tool_modules(
        tools_dir,
        {
            "staff_lookup": '''
                from aria.catalog import tool

                @tool
                def findStaff(fullName: str) -> list:
                    """Members of staff whose name matches."""
            '''
        },
    )
    paths = openapi_document()["paths"]
    paths["/people/search"] = {
        "get": operation("searchPeople", "PersonDto", parameters=[query_param("name", required=True)])
    }
    tools = bindings_with(
        tools_dir,
        findStaff={
            "operation": {"id": "searchPeople"},
            "parameters": {"fullName": "name"},
            "produces": {"staff_number": ["staffNo"]},
        },
    )
    modules = catalog_config(tools_dir).modules + ["staff_lookup"]
    return build(tools_dir, paths=paths, modules=modules, tools=tools)


def test_chain_starts_from_the_producer_the_request_gave_arguments_to(two_staff_producers):
    by_name = two_staff_producers.plan("staffVisits", filled={"findStaff": {"fullName"}})
    by_unit = two_staff_producers.plan("staffVisits", filled={"findUnits": {"title"}})

    assert [step.tool for step in by_name.steps] == ["findStaff", "staffVisits"]
    # The longer chain is used because only its first step has the arguments it needs.
    assert [step.tool for step in by_unit.steps] == ["findUnits", "unitPeople", "staffVisits"]


def test_producers_without_their_arguments_cannot_start_a_chain(two_staff_producers):
    plan = two_staff_producers.plan("staffVisits", filled={})

    assert not plan.complete
    # Either key would unblock the chain: a staff number directly, or a unit code for unitPeople.
    assert plan.missing_keys == ("Unit.code", "staff_number")


def test_diagnostic_planning_assumes_arguments_can_be_filled(two_staff_producers):
    plan = two_staff_producers.plan("staffVisits")

    assert [step.tool for step in plan.steps] == ["findStaff", "staffVisits"]
