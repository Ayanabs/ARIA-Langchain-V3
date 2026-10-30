"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDesignations() -> list:
    """Retrieves all HR designation records across the organisation."""


@tool
def searchHrDesignationsByName(name: str) -> list:
    """Searches HR designations by full or partial job title/name."""


@tool
def fetchHrDesignationsBySalaryCode(salaryCode: int) -> list:
    """Retrieves all designations associated with a specific salary scale code."""
