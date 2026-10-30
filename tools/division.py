"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDivisions() -> list:
    """Retrieves all institute division records."""


@tool
def fetchDivisionByCode(divisioncode: int) -> dict:
    """Retrieves division details by numeric primary division code (divisioncode)."""


@tool
def fetchDivisionsByHod(hodEmpno: int) -> list:
    """Retrieves division records led by a specific Head of Division (HOD) using their employee number
    (empno)."""


@tool
def fetchDivisionByName(name: str) -> dict:
    """Retrieves one division by its full name."""


@tool
def fetchDivisionByShortCode(shCode: str) -> dict:
    """Retrieves one division by its short code."""
