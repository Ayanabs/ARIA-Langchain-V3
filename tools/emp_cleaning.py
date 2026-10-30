"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpCleanings() -> list:
    """Retrieves duty assignments for cleaning and maintenance staff."""
