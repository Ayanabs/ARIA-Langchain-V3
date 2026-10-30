"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQInstitutes() -> list:
    """Retrieves university and educational institute master directory."""
