"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryScaleDetails() -> list:
    """Lists salary scale increment steps including salary code, grade, increment years, amount,
    and order."""
