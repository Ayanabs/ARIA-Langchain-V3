"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from aria.api import health
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
) -> FastAPI:
    """Build the service. Arguments exist so tests can inject settings and an offline transport."""
    settings = settings or get_settings()
    if preflight_on_startup is None:
        preflight_on_startup = settings.deployment.service.preflight_on_startup

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = None
        if preflight_on_startup:
            # In the background, so a slow dependency never delays the service accepting requests.
            task = asyncio.create_task(_run_startup_preflight(app, preflight_transport))
        yield
        if task and not task.done():
            task.cancel()

    app = FastAPI(title="ARIA", lifespan=lifespan)
    app.state.settings = settings
    app.state.preflight_report = None
    app.state.preflight_scheduled = preflight_on_startup
    app.include_router(health.router)
    return app
