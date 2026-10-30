"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpGrades() -> list:
    """Retrieves employee salary grade classification levels."""
