"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQClasses() -> list:
    """Retrieves academic degree class/grade honor classifications."""
