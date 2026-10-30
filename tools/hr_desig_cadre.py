"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDesigCadres() -> list:
    """Retrieves designation cadre allocation limits across divisions."""
