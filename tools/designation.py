"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDesignations() -> list:
    """Retrieves all designation job titles across the organisation."""
