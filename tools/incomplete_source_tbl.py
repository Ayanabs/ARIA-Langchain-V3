"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllIncompleteSources() -> list:
    """Lists incomplete data source flags and error logs including description and record
    identifier."""


@tool
def fetchIncompleteSourcesByDescription(description: str) -> list:
    """Lists incomplete source records filtered by error description text, returning the
    description and record ID."""
