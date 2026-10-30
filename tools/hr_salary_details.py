"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryDetails() -> list:
    """Retrieves monthly payroll processing records for all employees."""
