"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from aria.api import health
from aria.catalog.service import CatalogService
from aria.preflight import run_preflight
from aria.settings import Settings, get_settings

logger = logging.getLogger(__name__)


async def _run_startup_preflight(app: FastAPI, transport: httpx.AsyncBaseTransport | None) -> None:
    try:
        report = await run_preflight(app.state.settings, transport=transport)
    except Exception:
        logger.exception("preflight crashed")
        return
    app.state.preflight_report = report
    log = logger.warning if report.status != "ok" else logger.info
    log("preflight finished", extra={"preflight": report.to_dict()})


def create_app(
    settings: Settings | None = None,
    *,
    preflight_on_startup: bool | None = None,
    preflight_transport: httpx.AsyncBaseTransport | None = None,
    catalog_on_startup: bool | None = None,
    catalog_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Build the service. Arguments exist so tests can inject settings and offline transports."""
    settings = settings or get_settings()
    if preflight_on_startup is None:
        preflight_on_startup = settings.deployment.service.preflight_on_startup
    if catalog_on_startup is None:
        catalog_on_startup = settings.deployment.service.load_catalog_on_startup
    catalog_service = CatalogService(settings, transport=catalog_transport)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # In the background, so a slow dependency never delays the service accepting requests.
        tasks = []
        if preflight_on_startup:
            tasks.append(asyncio.create_task(_run_startup_preflight(app, preflight_transport)))
        if catalog_on_startup:
            tasks.append(asyncio.create_task(catalog_service.reload()))
        yield
        for task in tasks:
            if not task.done():
                task.cancel()

    app = FastAPI(title="ARIA", lifespan=lifespan)
    app.state.settings = settings
    app.state.preflight_report = None
    app.state.preflight_scheduled = preflight_on_startup
    app.state.catalog_service = catalog_service
    app.include_router(health.router)
    return app
