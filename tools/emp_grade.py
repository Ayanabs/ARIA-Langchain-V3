"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpGrades() -> list:
    """Lists salary grade classifications, returning grade ID, grade label, and full grade
    details."""
