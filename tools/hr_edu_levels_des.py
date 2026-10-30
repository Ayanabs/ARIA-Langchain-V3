"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrEduLevelsDes() -> list:
    """Lists detailed education level descriptions, returning the identifier and descriptive
    text for specific educational qualifications."""
