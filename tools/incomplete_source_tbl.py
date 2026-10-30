"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllIncompleteSources() -> list:
    """Retrieves incomplete data source flags and error log definitions."""


@tool
def fetchIncompleteSourcesByDescription(description: str) -> list:
    """Retrieves incomplete source records filtered by error description text."""
