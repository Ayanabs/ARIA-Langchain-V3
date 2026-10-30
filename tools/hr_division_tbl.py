"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDivisions() -> list:
    """Retrieves all HR division records."""


@tool
def searchHrDivisionsByName(name: str) -> list:
    """Searches HR division records by full or partial division title/name."""


@tool
def fetchHrDivisionsByCategory(category: str) -> list:
    """Retrieves HR division records matching a category code."""


@tool
def fetchHrDivisionsByShCode(shCode: str) -> list:
    """Retrieves HR division records matching short code/acronym (shCode)."""
