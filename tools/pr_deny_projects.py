"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrDenyProjects() -> list:
    """Lists denied project proposal records, returning identifier, reason, date time, user
    details and project code."""


@tool
def fetchPrDenyProjectsByPCode(pCode: str) -> list:
    """Lists denial records for a project by its code, returning id, reason, date time, and user
    type."""


@tool
def fetchPrDenyProjectsByReason(reason: str) -> list:
    """Lists denied projects filtered by a reason keyword, returning id, reason, date time, and
    user type."""
