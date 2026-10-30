"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllIssues() -> list:
    """Retrieves electronic timecard attendance discrepancy issues for all employees."""


@tool
def fetchIssuesByEmpNo(empNo: int) -> list:
    """Retrieves timecard attendance discrepancy issues for a specific employee by Employee Number
    (empNo)."""


@tool
def fetchIssuesByType(issueType: int) -> list:
    """Retrieves attendance issues filtered by issue type."""


@tool
def fetchIssueByAttDtId(attDtId: int) -> dict:
    """Retrieves the attendance issue recorded for one attendance date ID."""
