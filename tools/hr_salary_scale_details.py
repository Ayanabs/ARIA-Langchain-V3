"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryScaleDetails() -> list:
    """Retrieves detailed salary scale increment step breakdowns."""
