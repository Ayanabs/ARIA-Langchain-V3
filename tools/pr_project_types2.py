"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjectTypes2() -> list:
    """Lists all PR project types 2, returning id and pro type."""
