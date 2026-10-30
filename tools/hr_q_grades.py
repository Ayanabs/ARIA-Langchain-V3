"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQGrades() -> list:
    """Lists examination grade symbol records, returning grade number and grade name."""


@tool
def searchHrQGradesByName(name: str) -> list:
    """Lists grade records matching the name parameter, returning grade number and grade name."""
