"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchLeaveHeadPrsByEmpNo(empNo: int) -> list:
    """Lists project lead leave approval records for an employee by their number, returning the
    approval ID, employee number, and head employee number."""


@tool
def fetchLeaveHeadPrsByHodEmpNo(hodEmpNo: int) -> list:
    """Lists project lead leave approval records by a specific project head's employee number,
    returning the approval ID, employee number, and head employee number."""


@tool
def fetchLeaveHeadPrsByPrHeadEmpNo(prHeadEmpNo: int) -> list:
    """Lists leave applications reviewed by a specific project director or manager using their
    employee number, returning the approval ID, employee number, and head employee number."""
