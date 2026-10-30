"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryAllDetails() -> list:
    """Retrieves detailed salary slip breakdown calculations for all employees."""


@tool
def fetchHrSalaryAllDetailsByEmpNo(empNo: int) -> list:
    """Retrieves detailed salary breakdown calculations for a specific employee by Employee Number
    (empNo)."""
