"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDayTypes() -> list:
    """Lists all calendar day type classifications, returning the day type identifier and day
    type name."""
