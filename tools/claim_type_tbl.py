"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllClaimTypes() -> list:
    """Lists all official claim types, returning the claim type identifier and claim type name."""


@tool
def fetchClaimTypeByType(cType: str) -> dict:
    """Gets claim type details by description or name, returning ctype id and ctype."""
