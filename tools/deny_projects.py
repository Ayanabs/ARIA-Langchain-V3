"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDenyProjects() -> list:
    """Lists rejected project proposal records, returning the project identifier, reason for
    denial, and project code."""
