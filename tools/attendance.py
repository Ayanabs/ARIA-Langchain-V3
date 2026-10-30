"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllActualAttendanceByEmployee(empNo: int) -> list:
    """Retrieves the complete, full historical clock-in (entering) and clock-out (leaving) attendance
    logs for a specific employee (all records, complete history)."""


@tool
def fetchActualAttendanceByEmployeeAndDate(empNo: int, date: str) -> dict:
    """Retrieves the exact entering (in-time) and leaving (out-time) timestamps for an employee on a
    specific calendar date."""


@tool
def fetchActualAttendanceByDate(date: str) -> list:
    """Retrieves all employee clock-in (entering) and clock-out (leaving) records on a specific date."""
