import asyncio

import httpx
import pytest

from aria.calling.backend import BackendCallError, BackendInvoker
from aria.calling.chain import Selection, run_chain
from aria.calling.provenance import CALLER, PROMPT, KeyValue, accept_supplied_keys
from aria.calling.requests import ArgumentError, build_request
from aria.catalog.catalog import build_catalog
from tests.catalog_fixtures import METADATA, catalog_config, openapi_document, write_tool_modules


@pytest.fixture
def catalog(tmp_path):
    tools_dir = tmp_path / "tools"
    write_tool_modules(tools_dir)
    return build_catalog(catalog_config(tools_dir), openapi_document(), METADATA)


class FakeBackend:
    """Answers tool requests from canned data keyed by the filled-in path."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.requests = []

    async def __call__(self, tool, request):
        self.requests.append((request.path, request.query))
        key = request.path + (
            "?" + "&".join(f"{k}={v}" for k, v in request.query.items()) if request.query else ""
        )
        if key not in self.responses:
            raise BackendCallError(f"unexpected request {key}", status_code=404)
        return self.responses[key]


def run(catalog, goal, backend, **kwargs):
    filled = {tool: set(args) for tool, args in kwargs.get("arguments", {}).items()}
    plan = catalog.plan(goal, set(kwargs.get("supplied", {})), filled)
    return asyncio.run(run_chain(plan, catalog.tools, invoke=backend, **kwargs))


# --- A needs B needs C ------------------------------------------------------------------------


def test_three_step_chain_passes_keys_from_each_step_to_the_next(catalog):
    backend = FakeBackend(
        {
            "/units/search?title=Survey": [{"code": 7, "title": "Survey"}],
            "/units/7/people": [{"id": 9001, "staffNo": 1042, "fullName": "A. Person"}],
            "/people/1042/visits": [{"visitId": 1, "staffNo": 1042, "day": "2026-10-01"}],
        }
    )

    outcome = run(catalog, "staffVisits", backend, arguments={"findUnits": {"title": "Survey"}})

    assert outcome.status == "complete"
    assert [path for path, _ in backend.requests] == [
        "/units/search",
        "/units/7/people",
        "/people/1042/visits",
    ]
    assert outcome.goal_rows == [{"visitId": 1, "staffNo": 1042, "day": "2026-10-01"}]
    # The surrogate id 9001 is never used: the declared business key is.
    assert outcome.calls[2].arguments == {"staffNo": 1042}
    assert outcome.calls[1].key_sources == {"unitCode": "result:findUnits"}
    assert outcome.calls[2].key_sources == {"staffNo": "result:unitPeople"}


def test_ambiguous_producer_result_asks_the_user(catalog):
    backend = FakeBackend(
        {
            "/units/search?title=Survey": [{"code": 7, "title": "Survey"}],
            "/units/7/people": [
                {"staffNo": 1042, "fullName": "A. Person"},
                {"staffNo": 1043, "fullName": "B. Person"},
            ],
        }
    )

    outcome = run(catalog, "staffVisits", backend, arguments={"findUnits": {"title": "Survey"}})

    assert outcome.status == "needs_clarification"
    assert outcome.clarify_tool == "unitPeople"
    assert [row["staffNo"] for row in outcome.candidates] == [1042, 1043]
    # Nothing after the ambiguous step was called.
    assert len(backend.requests) == 2


def test_selected_subjects_fan_out_to_one_call_each(catalog):
    backend = FakeBackend(
        {
            "/units/search?title=Survey": [{"code": 7}],
            "/units/7/people": [{"staffNo": 1042}, {"staffNo": 1043}],
            "/people/1042/visits": [{"visitId": 1}],
            "/people/1043/visits": [{"visitId": 2}],
        }
    )

    def select_all(tool, rows):
        return Selection(rows=tuple(rows))

    outcome = run(
        catalog, "staffVisits", backend, arguments={"findUnits": {"title": "Survey"}}, select=select_all
    )

    assert outcome.status == "complete"
    assert sorted(row["visitId"] for row in outcome.goal_rows) == [1, 2]


def test_fan_out_beyond_the_limit_stops(catalog):
    backend = FakeBackend(
        {
            "/units/search?title=Survey": [{"code": 7}],
            "/units/7/people": [{"staffNo": number} for number in range(1, 6)],
        }
    )

    outcome = run(
        catalog,
        "staffVisits",
        backend,
        arguments={"findUnits": {"title": "Survey"}},
        select=lambda tool, rows: Selection(rows=tuple(rows)),
        max_fan_out=3,
    )

    assert outcome.status == "failed"
    assert "would need 5 calls; the limit is 3" in outcome.reason


def test_empty_producer_result_is_reported_missing(catalog):
    backend = FakeBackend({"/units/search?title=Nowhere": []})

    outcome = run(catalog, "staffVisits", backend, arguments={"findUnits": {"title": "Nowhere"}})

    assert outcome.status == "missing"
    assert outcome.reason == "findUnits returned no matching records"


def test_producer_row_without_the_key_field_is_not_used(catalog):
    backend = FakeBackend(
        {
            "/units/search?title=Survey": [{"code": 7}],
            "/units/7/people": [{"staffNo": None, "fullName": "A. Person"}],
        }
    )

    outcome = run(catalog, "staffVisits", backend, arguments={"findUnits": {"title": "Survey"}})

    assert outcome.status == "missing"
    assert "returned no staff_number value" in outcome.reason


def test_supplied_key_skips_its_producers(catalog):
    backend = FakeBackend({"/people/1042/visits": [{"visitId": 1}]})
    supplied = {"staff_number": KeyValue("staff_number", ("1042",), PROMPT)}

    outcome = run(catalog, "staffVisits", backend, supplied=supplied)

    assert outcome.status == "complete"
    assert outcome.calls[0].arguments == {"staffNo": 1042}
    assert outcome.calls[0].key_sources == {"staffNo": PROMPT}


def test_composite_key_is_passed_field_by_field(catalog):
    backend = FakeBackend(
        {
            "/memberships": [{"groupRef": "G/1", "seat": 3, "holder": "x"}],
            "/memberships/G%2F1/3": {"groupRef": "G/1", "seat": 3, "holder": "x"},
        }
    )

    outcome = run(catalog, "membershipBySeat", backend)

    assert outcome.status == "complete"
    # "/" inside a key value is encoded, so it cannot reach another endpoint.
    assert backend.requests[1][0] == "/memberships/G%2F1/3"


def test_backend_error_stops_the_chain(catalog):
    backend = FakeBackend({})

    outcome = run(catalog, "staffVisits", backend, arguments={"findUnits": {"title": "Survey"}})

    assert outcome.status == "failed"
    assert outcome.reason.startswith("findUnits failed: BackendCallError")


def test_incomplete_plan_is_not_run(catalog):
    backend = FakeBackend({})

    outcome = run(catalog, "staffLedger", backend)

    assert outcome.status == "missing"
    assert "Ledger.staffNo" in outcome.reason
    assert backend.requests == []


# --- key provenance ---------------------------------------------------------------------------


def test_invented_key_argument_is_rejected(catalog):
    backend = FakeBackend({})

    outcome = run(
        catalog,
        "staffVisits",
        backend,
        supplied={"staff_number": KeyValue("staff_number", (1042,), PROMPT)},
        arguments={"staffVisits": {"staffNo": 999}},
    )

    assert outcome.status == "failed"
    assert "key arguments staffNo must come from an earlier result" in outcome.reason
    assert backend.requests == []


def test_invented_key_on_a_later_step_stops_the_chain_before_any_call(catalog):
    backend = FakeBackend({"/units/search?title=Survey": [{"code": 7}]})

    outcome = run(
        catalog,
        "staffVisits",
        backend,
        arguments={"findUnits": {"title": "Survey"}, "staffVisits": {"staffNo": 999}},
    )

    assert outcome.status == "failed"
    assert backend.requests == []


def test_key_values_must_appear_in_the_prompt():
    accepted, rejected = accept_supplied_keys(
        {"staff_number": ("1042",), "Unit.code": (12,)},
        prompt="Visits by staff number 1042 in 2012",
    )

    assert accepted["staff_number"].source == PROMPT
    # 12 only appears inside 2012, which is not a mention of 12.
    assert [item.key_id for item in rejected] == ["Unit.code"]


def test_caller_identity_is_an_accepted_key_source():
    accepted, rejected = accept_supplied_keys(
        {"staff_number": (1042,)}, prompt="show my visits", caller_keys={"staff_number": ("1042",)}
    )

    assert accepted["staff_number"].source == CALLER
    assert rejected == []


# --- requests ---------------------------------------------------------------------------------


def test_request_arguments_are_checked(catalog):
    tool = catalog.tools["staffVisits"]

    with pytest.raises(ArgumentError, match="unknown arguments other"):
        build_request(tool, {"staffNo": 1, "other": 2})
    with pytest.raises(ArgumentError, match="missing required argument staffNo"):
        build_request(tool, {})
    with pytest.raises(ArgumentError, match="staffNo must be integer"):
        build_request(tool, {"staffNo": True})


def test_backend_invoker_forwards_the_callers_authorization(settings, catalog):
    seen = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json=[{"code": 7}])

    invoker = BackendInvoker(settings, authorization="Bearer abc", transport=httpx.MockTransport(handle))
    tool = catalog.tools["findUnits"]

    rows = asyncio.run(invoker(tool, build_request(tool, {"title": "Survey"})))

    assert rows == [{"code": 7}]
    assert seen == {"url": "http://backend.test/units/search?title=Survey", "authorization": "Bearer abc"}


def test_backend_invoker_reports_http_errors_without_the_filled_path(settings, catalog):
    invoker = BackendInvoker(settings, transport=httpx.MockTransport(lambda request: httpx.Response(403)))
    tool = catalog.tools["staffVisits"]

    with pytest.raises(BackendCallError) as raised:
        asyncio.run(invoker(tool, build_request(tool, {"staffNo": 1042})))

    assert raised.value.status_code == 403
    assert "1042" not in str(raised.value)
