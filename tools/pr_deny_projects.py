"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrDenyProjects() -> list:
    """Retrieves denied PR project proposal records."""


@tool
def fetchPrDenyProjectsByPCode(pCode: str) -> list:
    """Retrieves denial records for a specific project by Project Code (pCode )."""


@tool
def fetchPrDenyProjectsByReason(reason: str) -> list:
    """Retrieves denied projects filtered by denial reason keyword."""
