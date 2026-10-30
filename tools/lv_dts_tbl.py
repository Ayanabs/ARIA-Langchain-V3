"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllLeaveDates() -> list:
    """Lists leave date breakdown records for approved applications, returning id, leave
    identifier, date and number of days."""


@tool
def fetchLeaveDatesByLeaveDate(leaveDate: str) -> list:
    """Lists leave date records filtered by a specific calendar date, returning the ID, leave
    ID, date, and number of days."""
