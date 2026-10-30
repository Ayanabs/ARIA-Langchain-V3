import socket
import subprocess
import sys
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from aria.app import create_app
from tests.catalog_fixtures import METADATA, catalog_config, openapi_document, write_tool_modules
from tests.conftest import NetworkBlocked
from tests.test_preflight import FakeHosts


def test_health_responds_without_contacting_other_services(settings):
    with TestClient(create_app(settings, preflight_on_startup=False)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aria-test"
    assert body["preflight"] == {"status": "not_run"}


def test_health_reports_the_startup_preflight(settings):
    app = create_app(
        settings, preflight_on_startup=True, preflight_transport=httpx.MockTransport(FakeHosts().handle)
    )
    with TestClient(app) as client:
        body = client.get("/health").json()
        deadline = time.monotonic() + 5
        while body["preflight"]["status"] == "pending" and time.monotonic() < deadline:
            time.sleep(0.02)
            body = client.get("/health").json()
    assert body["preflight"]["status"] == "ok"
    assert body["preflight"]["checks"]["backend_openapi"] == "ok"


def test_health_reports_the_tool_catalog_loaded_at_startup(settings, tmp_path):
    tools_dir = tmp_path / "tools"
    write_tool_modules(tools_dir)
    settings.deployment.catalog = catalog_config(tools_dir)
    backend = settings.deployment.backend
    documents = {backend.openapi_path: openapi_document(), backend.metadata_schema_path: METADATA}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=documents[request.url.path]))

    app = create_app(settings, catalog_on_startup=True, catalog_transport=transport)
    with TestClient(app) as client:
        body = client.get("/health").json()
        deadline = time.monotonic() + 5
        while body["catalog"]["status"] != "ready" and time.monotonic() < deadline:
            time.sleep(0.02)
            body = client.get("/health").json()

    assert body["catalog"] == {"status": "ready", "tools_ready": 7, "tools_unavailable": 0}


def test_offline_tests_cannot_reach_the_network():
    with pytest.raises(NetworkBlocked):
        socket.create_connection(("192.0.2.1", 80), timeout=1)


HEAVY_MODULES = ("torch", "transformers", "sentence_transformers", "numpy", "langchain", "langchain_core")


def test_importing_the_application_stays_light():
    probe = (
        "import sys, aria.app, aria.preflight, aria.calling.chain; "
        f"print(','.join(m for m in {HEAVY_MODULES!r} if m in sys.modules))"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""
