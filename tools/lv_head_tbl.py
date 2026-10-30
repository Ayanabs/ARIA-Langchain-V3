"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllLeaveHeads() -> list:
    """Retrieves Head of Division (HOD) leave recommendation and approval records."""


@tool
def fetchLeaveHeadsByEmpNo(empNo: int) -> list:
    """Retrieves HOD leave recommendations for an employee by Employee Number (empNo )."""


@tool
def fetchLeaveHeadsByHodEmpNo(hodEmpNo: int) -> list:
    """Retrieves leave applications reviewed or recommended by a specific Head of Division using
    Head_EmpNo (hodEmpNo )."""
