"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllLeaveHeads() -> list:
    """Lists head of division leave recommendation records, returning hod identifier, employee
    number and hod employee number."""


@tool
def fetchLeaveHeadsByEmpNo(empNo: int) -> list:
    """Lists HOD leave recommendations for an employee by their number, returning the
    recommendation ID, employee number, and head employee number."""


@tool
def fetchLeaveHeadsByHodEmpNo(hodEmpNo: int) -> list:
    """Lists leave applications reviewed or recommended by a specific head of division using
    their employee number, returning the recommendation ID, employee number, and head employee
    number."""
