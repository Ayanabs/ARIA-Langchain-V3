"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllIssues() -> list:
    """Lists attendance discrepancy issues including employee number, description, issue type,
    and attendance date identifier."""


@tool
def fetchIssuesByEmpNo(empNo: int) -> list:
    """Lists attendance discrepancy issues for an employee by their number, returning the date
    ID, employee number, description, and issue type."""


@tool
def fetchIssuesByType(issueType: int) -> list:
    """Lists attendance issues filtered by a specific issue type, returning the date ID,
    employee number, description, and issue type."""


@tool
def fetchIssueByAttDtId(attDtId: int) -> dict:
    """Gets the attendance issue for an attendance date ID, returning the employee number,
    description and issue type."""
