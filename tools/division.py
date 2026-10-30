"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDivisions() -> list:
    """Lists division records, returning division code, name, short code, and head of division."""


@tool
def fetchDivisionByCode(divisioncode: int) -> dict:
    """Gets one division record selected by its numeric code, returning the name, short code,
    and head of division."""


@tool
def fetchDivisionsByHod(hodEmpno: int) -> list:
    """Lists divisions led by a specific employee number, returning the division name, short
    code, and director general."""


@tool
def fetchDivisionByName(name: str) -> dict:
    """Gets one division record selected by its full name, returning the code, short code, and
    head of division."""


@tool
def fetchDivisionByShortCode(shCode: str) -> dict:
    """Gets one division record selected by its short code, returning the name, numeric code,
    and head of division."""
