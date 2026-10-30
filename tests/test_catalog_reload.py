"""Rebuilding the catalog from the live contract, and what a failed reload leaves."""

import asyncio
import textwrap

import httpx

from aria.catalog.service import CatalogService
from tests.catalog_fixtures import METADATA, build, catalog_config, openapi_document
from tests.conftest import TEST_ENV


def contract_transport(responses: dict[str, httpx.Response]):
    def handle(request: httpx.Request) -> httpx.Response:
        return responses.get(request.url.path, httpx.Response(404))

    return httpx.MockTransport(handle)


def test_reload_builds_catalog_and_a_failed_reload_clears_it(settings, tools_dir):
    settings.deployment.catalog = catalog_config(tools_dir)
    backend = settings.deployment.backend
    good = {
        backend.openapi_path: httpx.Response(200, json=openapi_document()),
        backend.metadata_schema_path: httpx.Response(200, json=METADATA),
    }
    service = CatalogService(settings, transport=contract_transport(good))

    ready = asyncio.run(service.reload())
    assert ready.status == "ready"
    assert "staffVisits" in service.catalog.tools

    service.transport = contract_transport({backend.openapi_path: httpx.Response(503)})
    failed = asyncio.run(service.reload())

    assert failed.status == "failed"
    assert service.catalog.tools == {}
    assert "503" in failed.error or "HTTPStatusError" in failed.error


def test_contract_reads_send_the_configured_contract_token(make_settings, tools_dir):
    settings = make_settings(env={**TEST_ENV, "SPRING_BOOT_CONTRACT_TOKEN": "contract-secret-value"})
    settings.deployment.catalog = catalog_config(tools_dir)
    documents = {
        settings.deployment.backend.openapi_path: openapi_document(),
        settings.deployment.backend.metadata_schema_path: METADATA,
    }
    seen = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization"))
        return httpx.Response(200, json=documents[request.url.path])

    catalog = asyncio.run(CatalogService(settings, transport=httpx.MockTransport(handle)).reload())

    assert catalog.status == "ready"
    assert seen == ["Bearer contract-secret-value"] * 2
    assert "contract-secret-value" in settings.secret_values()


def test_tool_module_edits_are_picked_up_on_rebuild(tools_dir):
    assert build(tools_dir).tools["findUnits"].description == "Units whose title matches the given text."

    (tools_dir / "units.py").write_text(
        textwrap.dedent(
            '''
            from aria.catalog import tool

            @tool
            def findUnits(title: str) -> list:
                """Units by title, edited."""
            '''
        ),
        encoding="utf-8",
    )

    assert build(tools_dir).tools["findUnits"].description == "Units by title, edited."
