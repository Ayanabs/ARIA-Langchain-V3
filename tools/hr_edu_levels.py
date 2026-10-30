"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrEduLevels() -> list:
    """Lists education level master categories, returning the identifier and descriptive text
    for each standard education tier."""
