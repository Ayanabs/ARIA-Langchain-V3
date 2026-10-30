"""Hold the current tool catalog and rebuild it on schema reload."""

from __future__ import annotations

import asyncio
import logging

import httpx

from aria.catalog.catalog import ToolCatalog, build_catalog, failed_catalog
from aria.settings import Settings

logger = logging.getLogger(__name__)


class CatalogUnavailable(Exception):
    """The backend contract could not be read or the catalog could not be built."""


async def fetch_contract_documents(
    settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> tuple[dict, dict]:
    """Read the backend's OpenAPI document and entity metadata: metadata reads, never operational ones."""
    http = settings.deployment.http
    timeout = httpx.Timeout(http.read_timeout_seconds, connect=http.connect_timeout_seconds)
    base = settings.env.spring_boot_base_url.rstrip("/")
    backend = settings.deployment.backend
    headers = settings.contract_headers()
    async with httpx.AsyncClient(timeout=timeout, transport=transport, headers=headers) as client:
        openapi, metadata = await asyncio.gather(
            _get_json(client, base + backend.openapi_path),
            _get_json(client, base + backend.metadata_schema_path),
        )
    return openapi, metadata


async def _get_json(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.get(url)
        response.raise_for_status()
        document = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise CatalogUnavailable(f"could not read {url}: {type(error).__name__}") from error
    if not isinstance(document, dict):
        raise CatalogUnavailable(f"{url} did not return a JSON object")
    return document


class CatalogService:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self.catalog: ToolCatalog = failed_catalog("not loaded yet")
        self._reload_lock = asyncio.Lock()

    async def reload(self) -> ToolCatalog:
        """Rebuild the catalog from the live contract. On failure, no tool stays advertised."""
        async with self._reload_lock:
            try:
                openapi, metadata = await fetch_contract_documents(self.settings, self.transport)
                catalog = build_catalog(self.settings.deployment.catalog, openapi, metadata)
            except Exception as error:
                logger.exception("tool catalog reload failed")
                catalog = failed_catalog(f"{type(error).__name__}: {error}")
            self.catalog = catalog
            return catalog
