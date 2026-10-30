"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDependentRelationships() -> list:
    """Retrieves the complete master lookup table of family relationship definitions."""


@tool
def searchHrDependentRelationshipsByName(name: str) -> list:
    """Searches family relationship definitions by title name."""
