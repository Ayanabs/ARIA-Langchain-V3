"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchEmpShortLeavesByEmpNo(empNo: int) -> list:
    """Retrieves short leave records for one employee by employee number."""


@tool
def fetchEmpShortLeavesByAttDtId(attDtId: int) -> list:
    """Retrieves short leave records for one attendance date ID."""
