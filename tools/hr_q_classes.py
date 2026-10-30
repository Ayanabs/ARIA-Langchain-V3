"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQClasses() -> list:
    """Lists academic degree class records, returning identifier and description."""
