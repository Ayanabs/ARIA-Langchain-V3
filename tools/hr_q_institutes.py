"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQInstitutes() -> list:
    """Lists educational institute directory records, returning identifier, name, government
    status and local status."""
