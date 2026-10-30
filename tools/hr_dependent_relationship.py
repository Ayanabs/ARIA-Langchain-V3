"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDependentRelationships() -> list:
    """Lists family relationship definitions, returning relationship label and its corresponding
    ID."""


@tool
def searchHrDependentRelationshipsByName(name: str) -> list:
    """Lists family relationship definitions selected by title name, returning relationship
    identifier and relationship name."""
