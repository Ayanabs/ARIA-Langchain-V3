"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllMainSubDivisions() -> list:
    """Lists parent-child sub-division hierarchy mappings, returning division identifier, main
    division code and child division code."""


@tool
def fetchMainSubDivisionsByMainDivCode(mainDivCode: str) -> list:
    """Lists sub-division records selected by main division code, returning division ID, main
    division code and child division code."""


@tool
def fetchMainSubDivisionsByChildDivCode(childDivCode: int) -> list:
    """Lists parent division records selected by child division code, returning division ID,
    main division code and child division code."""
