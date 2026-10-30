"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDepDetails() -> list:
    """Retrieves dependent family member records for all employees."""


@tool
def fetchHrDepDetailsByEmployee(empNo: int) -> list:
    """Retrieves dependent family member records for a specific employee by Employee Number (empNo)."""


@tool
def fetchHrDepDetailsByRelationship(relationship: int) -> list:
    """Retrieves employee dependent records filtered by numeric family relationship ID."""


@tool
def searchHrDepDetailsByName(name: str) -> list:
    """Searches employee dependent records by full or partial dependent name."""
