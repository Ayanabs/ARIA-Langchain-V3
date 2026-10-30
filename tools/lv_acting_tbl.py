"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllLeaveActing() -> list:
    """Retrieves all leave acting cover arrangements across the entire organisation. Each record
    contains: Lv_Act_ID, Emp_No (absent employee), Act_Emp_No (substitute/covering officer),
    Leave_Start_Date, Leave_End_Date, and status."""


@tool
def fetchLeaveActingByEmployee(empNo: int) -> list:
    """Retrieves acting arrangement records for an employee taking leave (who acted on their behalf
    while they were absent)."""


@tool
def fetchLeaveActingByActingEmployee(actEmpNo: int) -> list:
    """Retrieves leave acting cover records where a specific employee (actEmpNo) acted or covered
    duties for another employee on leave."""
