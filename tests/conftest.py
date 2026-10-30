"""Shared test setup.

Default tests are offline: any connection or name lookup outside loopback fails immediately, so a
test that would reach Redis, a database, the backend or a model host cannot hang. Tests marked
`live` are exempt and run separately with `pytest -m live`.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
import yaml

from aria.settings import EnvSettings, Settings, load_settings
from tests.catalog_fixtures import write_tool_modules

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


class NetworkBlocked(RuntimeError):
    pass


def _is_loopback(address) -> bool:
    host = address[0] if isinstance(address, tuple) else address
    return host in LOOPBACK_HOSTS


@pytest.fixture(autouse=True)
def block_network(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        return
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    # Loopback stays open: asyncio on Windows builds its self-pipe from a loopback socket pair.
    def guarded_connect(sock, address):
        if not _is_loopback(address):
            raise NetworkBlocked(f"offline test tried to connect to {address!r}")
        return real_connect(sock, address)

    def guarded_connect_ex(sock, address):
        if not _is_loopback(address):
            raise NetworkBlocked(f"offline test tried to connect to {address!r}")
        return real_connect_ex(sock, address)

    def guarded_getaddrinfo(host, *args, **kwargs):
        if host not in LOOPBACK_HOSTS and host is not None:
            raise NetworkBlocked(f"offline test tried to resolve {host!r}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    """Keep the developer's shell environment out of settings under test."""
    for field_name in EnvSettings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)


# Deliberately not the deployed model names: settings must work for any configured model.
TEST_ENV = {
    "SPRING_BOOT_BASE_URL": "http://backend.test",
    "OPENAI_API_BASE": "http://models.test/v1",
    "OPENAI_API_KEY": "tool-secret-value",
    "MODEL_NAME": "router-model",
    "MODEL_NATIVE_API_BASE": "http://models.test",
    "GENERAL_OPENAI_API_BASE": "http://models.test/v1",
    "GENERAL_MODEL_NAME": "writer-model",
    "GENERAL_MODEL_NATIVE_API_BASE": "http://models.test",
    "EMBEDDING_API_BASE": "http://embeddings.test",
    "EMBEDDING_MODEL_NAME": "embedder",
    "RAG_SERVICE_URL": "http://rag.test/api/search",
    "REDIS_HOST": "redis.test",
    "CHATS_DB_HOST": "chats.test",
    "PROMPTS_DB_HOST": "prompts.test",
}


def profile(**overrides) -> dict:
    values = {
        "provider": "ollama",
        "context_tokens": 8192,
        "input_budget_tokens": 4096,
        "max_output_tokens": 512,
        "tool_calling": True,
        "structured_output": True,
        "output_tokens_per_second": 15,
        "max_tools_per_call": 8,
        "shortlist_k": 8,
        "timeout_seconds": 30,
    }
    values.update(overrides)
    return values


def deployment_config(**overrides) -> dict:
    config = {
        "service": {"name": "aria-test", "preflight_on_startup": False, "load_catalog_on_startup": False},
        "backend": {"openapi_path": "/contract/openapi", "metadata_schema_path": "/contract/entities"},
        "http": {"connect_timeout_seconds": 1, "read_timeout_seconds": 2, "retries": 0},
        "preflight": {"timeout_seconds": 2},
        "models": {"profiles": {"router-model": profile(), "writer-model": profile(max_output_tokens=768)}},
    }
    config.update(overrides)
    return config


@pytest.fixture
def write_config(tmp_path: Path):
    """Write an env file and deployment YAML, returning a loader for them."""

    def write(env: dict | None = None, config: dict | None = None) -> tuple[Path, Path]:
        env_path = tmp_path / "test.env"
        env_values = TEST_ENV if env is None else env
        env_path.write_text(
            "\n".join(f"{key}={value}" for key, value in env_values.items()), encoding="utf-8"
        )
        config_path = tmp_path / "aria.yaml"
        config_path.write_text(yaml.safe_dump(config or deployment_config()), encoding="utf-8")
        return env_path, config_path

    return write


@pytest.fixture
def make_settings(write_config):
    def make(env: dict | None = None, config: dict | None = None) -> Settings:
        env_path, config_path = write_config(env, config)
        return load_settings(env_file=env_path, config_file=config_path)

    return make


@pytest.fixture
def settings(make_settings) -> Settings:
    return make_settings()


@pytest.fixture
def tools_dir(tmp_path):
    """The fake tool modules from catalog_fixtures, written to a temporary tools folder."""
    directory = tmp_path / "tools"
    write_tool_modules(directory)
    return directory
