"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryScales() -> list:
    """Retrieves salary scale definition master records."""
