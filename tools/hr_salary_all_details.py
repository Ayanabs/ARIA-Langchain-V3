"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryAllDetails() -> list:
    """Lists employee salary slip details including current salary, increment value, grade, and
    paid date."""


@tool
def fetchHrSalaryAllDetailsByEmpNo(empNo: int) -> list:
    """Lists detailed salary breakdown calculations for an employee selected by employee number,
    returning current salary, grade, increment value and paid date."""
