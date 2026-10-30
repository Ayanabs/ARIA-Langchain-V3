"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpLeaves() -> list:
    """Lists employee leave records, returning leave ID, employee number, type ID, and days
    count."""


@tool
def fetchEmpLeavesByEmployee(empNo: int) -> list:
    """Lists leave records for an employee selected by their number, returning the type ID,
    number of days, and attendance date ID."""


@tool
def fetchEmpLeavesByType(leaveTypeId: int) -> list:
    """Lists leave records filtered by a specific type ID, returning the employee number, number
    of days, and attendance date ID."""


@tool
def fetchOverseasEmpLeaves() -> list:
    """Lists overseas leave records for employees, returning leave ID, employee number, leave
    type ID and number of days."""
