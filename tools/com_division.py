"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllComDivisions() -> list:
    """Retrieves internal sub-division hierarchy linkage records (divId, mdivCode, tdivCode)
    NOTE: This is NOT the Communication Division (COM) or general division catalog."""
