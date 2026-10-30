"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpCleanings() -> list:
    """Lists cleaning staff duty assignments, returning employee ID, name, address, and
    telephone number."""
