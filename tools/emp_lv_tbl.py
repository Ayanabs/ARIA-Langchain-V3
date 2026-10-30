"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpLeaves() -> list:
    """Retrieves all employee leave records across the entire organisation. Each record contains:
    empNo, leaveTypeId, startDate, endDate, leaveDays count, reason, and approval status. Use
    for organisation-wide leave auditing."""


@tool
def fetchEmpLeavesByEmployee(empNo: int) -> list:
    """Retrieves leave records and leave history for a specific employee by employee number (empNo)."""


@tool
def fetchEmpLeavesByType(leaveTypeId: int) -> list:
    """Retrieves leave records filtered by a specific leave type ID."""


@tool
def fetchOverseasEmpLeaves() -> list:
    """Retrieves all overseas private and official foreign leave records for employees. Contains
    details of international travel approvals and duration."""
