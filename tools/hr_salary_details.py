"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryDetails() -> list:
    """Lists monthly payroll records including salary code, grade, initial value, and initial
    step."""
