import asyncio
import json

import httpx
import pytest

from aria.preflight import CheckStatus, run_preflight, summarize_openapi
from tests.conftest import TEST_ENV, deployment_config, profile

OPENAPI_DOCUMENT = {
    "openapi": "3.0.1",
    "paths": {
        "/records": {"get": {"operationId": "listRecords"}, "parameters": []},
        "/records/{code}": {"get": {"operationId": "getRecordByCode"}},
    },
}


class FakeHosts:
    """An offline stand-in for the model host and backend that records every request."""

    def __init__(self, model_max=32768, loaded_context=8192, openapi=None, missing_models=()):
        self.model_max = model_max
        self.loaded_context = loaded_context
        self.openapi = OPENAPI_DOCUMENT if openapi is None else openapi
        self.missing_models = set(missing_models)
        self.requests: list[tuple[str, str]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append((request.method, request.url.path))
        path = request.url.path
        if path == "/api/show":
            if json.loads(request.content)["model"] in self.missing_models:
                return httpx.Response(404, json={"error": "not found"})
            return httpx.Response(200, json={"model_info": {"somearch.context_length": self.model_max}})
        if path == "/api/ps":
            loaded = (
                []
                if self.loaded_context is None
                else [
                    {"name": "router-model", "context_length": self.loaded_context},
                    {"name": "writer-model", "context_length": self.loaded_context},
                ]
            )
            return httpx.Response(200, json={"models": loaded})
        if path == "/contract/openapi":
            return httpx.Response(200, json=self.openapi)
        if path == "/contract/entities":
            return httpx.Response(200, json={"entities": []})
        return httpx.Response(404)


def _run(settings, hosts: FakeHosts):
    return asyncio.run(run_preflight(settings, transport=httpx.MockTransport(hosts.handle)))


def _check(report, name):
    return next(check for check in report.checks if check.name == name)


def test_everything_reachable_and_consistent_passes(settings):
    report = _run(settings, FakeHosts())
    assert report.status == CheckStatus.OK, report.to_dict()


def test_preflight_reads_only_metadata_and_never_calls_a_model(settings):
    hosts = FakeHosts()
    _run(settings, hosts)
    paths = {path for _, path in hosts.requests}
    assert paths <= {"/api/show", "/api/ps", "/contract/openapi", "/contract/entities"}


def test_configured_context_above_the_model_maximum_fails(settings):
    report = _run(settings, FakeHosts(model_max=4096))
    check = _check(report, "model_context:tool")
    assert check.status == CheckStatus.FAIL
    assert check.data["modelMaxContext"] == 4096
    assert report.status == CheckStatus.FAIL


def test_a_model_missing_from_the_host_fails(settings):
    report = _run(settings, FakeHosts(missing_models={"writer-model"}))
    assert _check(report, "model_context:synthesis").status == CheckStatus.FAIL
    assert _check(report, "model_context:tool").status == CheckStatus.OK


def test_a_model_loaded_with_another_context_is_a_warning(settings):
    report = _run(settings, FakeHosts(loaded_context=16384))
    check = _check(report, "model_context:tool")
    assert check.status == CheckStatus.WARN
    assert check.data["loadedContext"] == 16384


def test_a_model_not_yet_loaded_is_fine(settings):
    report = _run(settings, FakeHosts(loaded_context=None))
    assert _check(report, "model_context:tool").status == CheckStatus.OK


def test_missing_native_api_base_fails_because_context_cannot_be_set(make_settings):
    env = {key: value for key, value in TEST_ENV.items() if key != "MODEL_NATIVE_API_BASE"}
    report = _run(make_settings(env=env), FakeHosts())
    assert _check(report, "config").status == CheckStatus.FAIL
    assert _check(report, "model_context:tool").status == CheckStatus.FAIL


def test_unset_optional_services_are_warnings(make_settings):
    env = {key: value for key, value in TEST_ENV.items() if key != "REDIS_HOST"}
    check = _check(_run(make_settings(env=env), FakeHosts()), "config")
    assert check.status == CheckStatus.WARN
    assert check.data["unset"] == ["REDIS_HOST"]


def test_duplicate_operation_ids_are_reported(settings):
    duplicated = {
        "openapi": "3.0.1",
        "paths": {"/a": {"get": {"operationId": "read"}}, "/b": {"get": {"operationId": "read"}}},
    }
    check = _check(_run(settings, FakeHosts(openapi=duplicated)), "backend_openapi")
    assert check.status == CheckStatus.WARN
    assert check.data["duplicateOperationIds"] == ["read"]


def test_a_non_openapi_document_fails(settings):
    check = _check(_run(settings, FakeHosts(openapi={"hello": "world"})), "backend_openapi")
    assert check.status == CheckStatus.FAIL


def test_unreachable_hosts_fail_without_hanging(settings):
    def refuse(request):
        raise httpx.ConnectError("refused", request=request)

    report = asyncio.run(run_preflight(settings, transport=httpx.MockTransport(refuse)))
    assert all(check.status == CheckStatus.FAIL for check in report.checks if check.name != "config")


def test_openapi_summary_counts_operations_without_ids():
    document = {"openapi": "3.0.1", "paths": {"/x": {"get": {}, "post": {"operationId": "createX"}}}}
    summary = summarize_openapi(document)
    assert summary["operations"] == 2
    assert summary["operationsWithoutId"] == 1


@pytest.mark.live
def test_live_preflight_against_configured_servers():
    from aria.settings import load_settings

    report = asyncio.run(run_preflight(load_settings()))
    assert report.status != CheckStatus.FAIL, report.to_dict()


def llama_cpp_settings(make_settings, context_tokens=8192):
    config = deployment_config(
        models={
            "profiles": {
                "router-model": profile(provider="llama_cpp", context_tokens=context_tokens),
                "writer-model": profile(provider="llama_cpp", context_tokens=context_tokens),
            }
        }
    )
    env = {key: value for key, value in TEST_ENV.items() if "NATIVE" not in key}
    return make_settings(env=env, config=config)


def llama_cpp_host(slot_context=16384, served=("router-model", "writer-model")):
    def handle(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": name} for name in served]})
        if path == "/props":
            return httpx.Response(200, json={"default_generation_settings": {"n_ctx": slot_context}})
        return FakeHosts().handle(request)

    return httpx.MockTransport(handle)


def test_llama_cpp_context_fits_the_host_slot(make_settings):
    settings = llama_cpp_settings(make_settings)

    report = asyncio.run(run_preflight(settings, transport=llama_cpp_host()))

    check = _check(report, "model_context:tool")
    assert check.status == CheckStatus.OK
    assert check.data == {"model": "router-model", "requestedContext": 8192, "slotContext": 16384}
    # llama.cpp needs no native API base; only Ollama does.
    assert _check(report, "config").status != CheckStatus.FAIL


def test_llama_cpp_context_larger_than_the_host_slot_fails(make_settings):
    settings = llama_cpp_settings(make_settings, context_tokens=32768)

    report = asyncio.run(run_preflight(settings, transport=llama_cpp_host(slot_context=16384)))

    assert _check(report, "model_context:tool").status == CheckStatus.FAIL


def test_llama_cpp_model_not_served_fails(make_settings):
    settings = llama_cpp_settings(make_settings)

    report = asyncio.run(run_preflight(settings, transport=llama_cpp_host(served=("writer-model",))))

    assert _check(report, "model_context:tool").detail == "model is not served by the host"
    assert _check(report, "model_context:synthesis").status == CheckStatus.OK
