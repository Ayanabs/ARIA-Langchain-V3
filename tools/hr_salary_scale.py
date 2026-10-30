"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryScales() -> list:
    """Lists salary scale definitions including salary code, grade, salary scale identifier, and
    record id."""
