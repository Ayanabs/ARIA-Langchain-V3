"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllComDivisions() -> list:
    """Lists internal sub-division hierarchy linkage records, returning the division identifier,
    main division code, and target division code."""
