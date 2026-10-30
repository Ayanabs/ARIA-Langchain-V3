"""Request traces: what the pipeline records, how history is stored, and the admin routes."""

import asyncio
import contextlib
import json
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from aria.api.observability import local_admin_only
from aria.app import create_app
from aria.catalog.catalog import build_catalog
from aria.models.client import ModelError, ModelReply
from aria.observability.store import PromptStore
from aria.observability.trace import RequestTrace
from aria.pipeline import answer_question
from aria.prompts import PromptsConfig
from tests.catalog_fixtures import METADATA, catalog_config, openapi_document

PROMPTS = PromptsConfig(tool_selection="Choose.", synthesis="Answer.", conversation="Chat.")


class FakeModel:
    def __init__(self, role, replies):
        self.role = SimpleNamespace(
            role=role, name=f"{role}-model", profile=SimpleNamespace(shortlist_k=10, input_budget_tokens=4000)
        )
        self.replies = list(replies)

    async def complete(self, messages, **kwargs):
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        content = reply if isinstance(reply, str) else json.dumps(reply)
        return ModelReply(content, [], 120, 15, 0, 150, 900)


class FakeBackend:
    def __init__(self, responses):
        self.responses = responses

    async def __call__(self, tool, request):
        query = "&".join(f"{name}={value}" for name, value in request.query.items())
        key = request.path + (f"?{query}" if query else "")
        return self.responses[key]


@pytest.fixture
def catalog(tools_dir):
    return build_catalog(catalog_config(tools_dir), openapi_document(), METADATA)


def run(catalog, question, decision, backend, synthesis_replies=("Here is the answer.",)):
    trace = RequestTrace(question, user_key="u1", username="analyst")
    tool_model = FakeModel("tool", [decision])
    synthesis_model = FakeModel("synthesis", list(synthesis_replies))
    coroutine = answer_question(
        question,
        catalog=catalog,
        tool_model=tool_model,
        synthesis_model=synthesis_model,
        invoke=backend,
        prompts=PROMPTS,
        max_fan_out=20,
        trace=trace,
    )
    # A model failure is raised after being recorded; the trace is what these tests inspect.
    with contextlib.suppress(ModelError):
        asyncio.run(coroutine)
    return trace


CHAIN_DECISION = {
    "route": "tools",
    "goal_tool": "staffVisits",
    "arguments": {"findUnits": {"title": "Survey"}},
}
CHAIN_BACKEND = {
    "/units/search?title=Survey": [{"code": 7}],
    "/units/7/people": [{"staffNo": 1042}],
    "/people/1042/visits": [{"visitId": 1}, {"visitId": 2}],
}


def test_a_chained_answer_records_every_step(catalog):
    trace = run(catalog, "staff visits for unit Survey", CHAIN_DECISION, FakeBackend(CHAIN_BACKEND))
    record = trace.to_console()

    assert record["status"] == "published"
    assert record["route"] == "database"
    events = [event["event"] for event in record["flow"]]
    assert events[:4] == ["received", "tool_search", "model_call", "tool_selection"]
    assert events.count("tool_call") == 3 and events[-1] == "finished"
    stages = {span["stage"] for span in record["spans"]}
    assert stages == {"tool_search", "tool_selection", "key_chain", "synthesis"}
    assert [call["role"] for call in record["modelCalls"]] == ["tool", "synthesis"]

    details = record["details"]
    assert details["tool_selection"]["model_decision"] == json.dumps(CHAIN_DECISION)
    assert [step["tool"] for step in details["plan"]["steps"]] == ["findUnits", "unitPeople", "staffVisits"]
    calls = details["tool_calls"]["calls"]
    assert [call["operation"] for call in calls] == [
        "GET /units/search",
        "GET /units/{code}/people",
        "GET /people/{staffNo}/visits",
    ]
    assert calls[2]["records"] == 2 and calls[2]["key_sources"] == {"staffNo": "result:unitPeople"}
    assert all(call["duration_ms"] is not None for call in calls)
    assert record["issues"] == []
    assert trace.answer == "Here is the answer."


def test_a_model_timeout_is_explained(catalog):
    trace = run(catalog, "staff visits", ModelError("timeout", "tool model call timed out"), FakeBackend({}))
    record = trace.to_console()

    assert record["status"] == "error" and record["failure"] == "timeout"
    [found] = record["issues"]
    assert found["code"] == "model_timeout" and found["severity"] == "error"
    assert found["title"] == "Model call timed out" and found["hint"]
    assert record["modelCalls"][0]["error_kind"] == "timeout"


def test_an_invented_key_is_rejected_with_its_reason(catalog):
    decision = {"route": "tools", "goal_tool": "staffVisits", "arguments": {"staffVisits": {"staffNo": 999}}}
    trace = run(catalog, "staff visits please", decision, FakeBackend({}))

    codes = [found["code"] for found in trace.to_console()["issues"]]
    assert "argument_rejected" in codes
    assert "'999' is not in the prompt" in trace.details["tool_selection"]["rejected"][0]


def test_ambiguous_matches_are_reported_as_a_question_for_the_user(catalog):
    backend = FakeBackend({"/units/search?title=Survey": [{"code": 7}, {"code": 8}]})
    trace = run(catalog, "staff visits for unit Survey", CHAIN_DECISION, backend)

    codes = [found["code"] for found in trace.to_console()["issues"]]
    assert codes == ["ambiguous_subject"]
    assert trace.details["tool_calls"]["candidates"] == 2


def test_backend_errors_carry_their_status_code(catalog):
    class FailingBackend:
        async def __call__(self, tool, request):
            from aria.calling.backend import BackendCallError

            raise BackendCallError("GET /units/search returned 503", status_code=503)

    trace = run(catalog, "staff visits for unit Survey", CHAIN_DECISION, FailingBackend())

    [found] = trace.to_console()["issues"]
    assert found["code"] == "backend_error"
    assert trace.details["tool_calls"]["calls"][0]["status_code"] == 503


# --- prompt history -------------------------------------------------------------------------


def make_record(index, started=None, user="u1", status="published"):
    trace = RequestTrace(f"question {index}", user_key=user, username=user)
    if started is not None:
        trace.started_at = started
    trace.finish(status)
    return trace.to_prompt_record()


def test_history_is_newest_first_and_bounded(tmp_path):
    store = PromptStore(tmp_path / "history.jsonl", max_entries=3, retention_days=30)
    for index in range(8):
        store.append(make_record(index))

    assert [record["prompt"] for record in store.records()] == ["question 7", "question 6", "question 5"]
    # Compaction keeps the file from growing past twice the limit.
    assert len((tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()) <= 6


def test_history_drops_records_past_retention(tmp_path):
    store = PromptStore(tmp_path / "history.jsonl", max_entries=10, retention_days=1)
    store.append(make_record(1, started=time.time() - 3 * 86400))
    store.append(make_record(2))

    assert [record["prompt"] for record in store.records()] == ["question 2"]


# --- admin routes ---------------------------------------------------------------------------


@pytest.fixture
def admin_client(settings, tmp_path):
    settings.deployment.observability.prompt_history_file = tmp_path / "history.jsonl"
    app = create_app(settings, preflight_on_startup=False, catalog_on_startup=False)
    app.dependency_overrides[local_admin_only] = lambda: None
    store = app.state.prompt_store
    store.append(make_record(1, user="alice"))
    store.append(make_record(2, user="bob", status="error"))
    with TestClient(app) as client:
        yield client


ADMIN_PREFIXES = ["/api/admin/observability", "/api/admin/console/gateway/api/admin/observability"]


@pytest.mark.parametrize("prefix", ADMIN_PREFIXES)
def test_prompt_history_routes_use_the_console_shapes(admin_client, prefix):
    page = admin_client.get(f"{prefix}/prompts", params={"status": "error"}).json()
    assert page["total"] == 1 and page["pageSize"] == 50 and page["enabled"] is True
    assert "trace" not in page["items"][0]

    request_id = page["items"][0]["id"]
    detail = admin_client.get(f"{prefix}/prompts/{request_id}").json()
    assert detail["trace"]["traceId"] == detail["trace_id"]
    assert admin_client.get(f"{prefix}/traces/{detail['trace_id']}").json()["status"] == "error"

    users = admin_client.get(f"{prefix}/users").json()
    assert [user["username"] for user in users["items"]] == ["alice", "bob"]
    summary = admin_client.get(prefix).json()
    assert summary["requestCount"] == 2 and summary["outcomes"] == {"error": 1, "published": 1}


def test_unknown_prompt_is_not_found(admin_client):
    assert admin_client.get("/api/admin/observability/prompts/nope").status_code == 404


def test_analytics_are_refused_to_other_machines(settings):
    app = create_app(settings, preflight_on_startup=False, catalog_on_startup=False)
    with TestClient(app) as client:  # the test client's address is not a loopback address
        response = client.get("/api/admin/observability/prompts")

    assert response.status_code == 403
    assert "limited to this machine" in response.json()["detail"]
