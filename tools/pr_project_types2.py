"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjectTypes2() -> list:
    """Retrieves all PR project types 2."""
