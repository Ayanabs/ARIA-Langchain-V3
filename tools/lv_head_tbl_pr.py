"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchLeaveHeadPrsByEmpNo(empNo: int) -> list:
    """Retrieves project lead leave approval records for an employee by Employee Number (empNo )."""


@tool
def fetchLeaveHeadPrsByHodEmpNo(hodEmpNo: int) -> list:
    """Retrieves project lead leave approval records by Project Head Employee Number (hodEmpNo )."""


@tool
def fetchLeaveHeadPrsByPrHeadEmpNo(prHeadEmpNo: int) -> list:
    """Retrieves leave applications reviewed by a specific Project Director/Manager using PrHead_EmpNo."""
