"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrEduLevelsDes() -> list:
    """Retrieves education level detailed descriptions."""
