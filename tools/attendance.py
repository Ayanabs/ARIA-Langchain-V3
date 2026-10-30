"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllActualAttendanceByEmployee(empNo: int) -> list:
    """Lists all historical attendance records for a specific employee, returning the employee
    number, date, in time, and out time."""


@tool
def fetchActualAttendanceByEmployeeAndDate(empNo: int, date: str) -> dict:
    """Gets the attendance record for a specific employee on a specific date, returning the
    employee number, date, in time, and out time."""


@tool
def fetchActualAttendanceByDate(date: str) -> list:
    """Lists employee attendance records for a specific date, returning the employee number,
    date, in time, and out time."""
