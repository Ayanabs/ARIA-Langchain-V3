"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQOLSubjects() -> list:
    """Lists O/L subject directory records, returning subject code and subject name."""
