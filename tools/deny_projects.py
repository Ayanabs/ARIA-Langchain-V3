"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDenyProjects() -> list:
    """Retrieves rejected or denied project proposal records."""
