"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrEduLevels() -> list:
    """Retrieves education level master categories."""
