"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllSaLocations() -> list:
    """Lists location records, returning the location ID, building ID, division ID, location
    details and short form."""
