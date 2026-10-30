"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllLeaveDates() -> list:
    """Retrieves leave date breakdown records for approved leave applications."""


@tool
def fetchLeaveDatesByLeaveDate(leaveDate: str) -> list:
    """Retrieves leave date records filtered by calendar date (leaveDate, Format: YYYY-MM-DD)."""
