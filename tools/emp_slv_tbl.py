"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchEmpShortLeavesByEmpNo(empNo: int) -> list:
    """Lists short leave records for an employee selected by employee number, returning leave
    type, comment, start time, and end time."""


@tool
def fetchEmpShortLeavesByAttDtId(attDtId: int) -> list:
    """Lists short leave records for an attendance date ID, returning the employee number, start
    time, and end time."""
