"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllClaimTypes() -> list:
    """Retrieves all official claim types."""


@tool
def fetchClaimTypeByType(cType: str) -> dict:
    """Retrieves claim type details by description or name (cType)."""
