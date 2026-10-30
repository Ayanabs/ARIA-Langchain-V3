"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQHiEdus() -> list:
    """Retrieves higher education qualification master list."""


@tool
def fetchHrQHieduByEmpNo(empNo: str) -> list:
    """Retrieves higher education qualifications for a specific employee by Employee Number (empNo )."""
