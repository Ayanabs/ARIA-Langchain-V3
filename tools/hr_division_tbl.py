"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDivisions() -> list:
    """Lists all HR division records, returning the code, name, short code and category for each
    organizational unit."""


@tool
def searchHrDivisionsByName(name: str) -> list:
    """Lists division records matching the name parameter, returning division code, division
    title, short code and category."""


@tool
def fetchHrDivisionsByCategory(category: str) -> list:
    """Lists division records selected by category code, returning division code, division, sh
    code, and category."""


@tool
def fetchHrDivisionsByShCode(shCode: str) -> list:
    """Lists division records selected by short code, returning division code, division, sh
    code, and category."""
