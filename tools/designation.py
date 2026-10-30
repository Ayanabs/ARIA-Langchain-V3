"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDesignations() -> list:
    """Lists all designation job titles across the organisation, returning the designation code,
    designation name, and main identifier."""
