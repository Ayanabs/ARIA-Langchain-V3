"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDayTypes() -> list:
    """Retrieves all calendar day type classifications."""
