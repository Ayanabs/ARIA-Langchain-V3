"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDesigCadres() -> list:
    """Lists designation cadre allocation limits, returning designation code and various
    capacity allocation fields."""
