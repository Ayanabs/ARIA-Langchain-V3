"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQGrades() -> list:
    """Retrieves examination grade symbols and pass levels."""


@tool
def searchHrQGradesByName(name: str) -> list:
    """Searches examination grade symbols by grade name or code."""
