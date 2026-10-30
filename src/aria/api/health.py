"""Liveness and readiness summary. Never contacts other services itself."""

from __future__ import annotations

from fastapi import APIRouter, Request

from aria import __version__

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    state = request.app.state
    report = state.preflight_report
    if report is None:
        preflight = {"status": "pending" if state.preflight_scheduled else "not_run"}
    else:
        preflight = {
            "status": report.status.value,
            "checks": {check.name: check.status.value for check in report.checks},
        }
    return {
        "status": "ok",
        "service": state.settings.deployment.service.name,
        "version": __version__,
        "preflight": preflight,
    }
