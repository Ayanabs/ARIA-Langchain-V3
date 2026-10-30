"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllMainSubDivisions() -> list:
    """Retrieves parent-child sub-division hierarchy mappings."""


@tool
def fetchMainSubDivisionsByMainDivCode(mainDivCode: str) -> list:
    """Retrieves sub-divisions belonging to a specific parent division using mainDivCode."""


@tool
def fetchMainSubDivisionsByChildDivCode(childDivCode: int) -> list:
    """Retrieves parent division mapping for a specific sub-division using childDivCode."""
