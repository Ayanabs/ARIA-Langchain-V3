"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDesignations() -> list:
    """Lists all HR designation records, returning the code, full name, salary code and cadre
    type for each position."""


@tool
def searchHrDesignationsByName(name: str) -> list:
    """Lists HR designations selected by job title name, returning designation code, designation
    name, salary code, and cadre."""


@tool
def fetchHrDesignationsBySalaryCode(salaryCode: int) -> list:
    """Lists designation records selected by salary code, returning desig code, designation,
    salary code, and ap cadre."""
