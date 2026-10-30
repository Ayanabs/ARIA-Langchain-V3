"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllLeaveActing() -> list:
    """Lists leave acting arrangements including absent employee number, covering officer
    number, and leave action identifier."""


@tool
def fetchLeaveActingByEmployee(empNo: int) -> list:
    """Lists acting arrangement records for an employee on leave, returning the acting ID,
    original employee number, and acting employee number."""


@tool
def fetchLeaveActingByActingEmployee(actEmpNo: int) -> list:
    """Lists leave acting records where an employee covered duties for another, returning the
    acting ID, original employee number, and acting employee number."""
