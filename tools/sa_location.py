"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllSaLocations() -> list:
    """Retrieves Space Applications Division satellite ground station and field site locations."""
