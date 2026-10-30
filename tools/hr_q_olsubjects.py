"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQOLSubjects() -> list:
    """Retrieves G.C.E. Ordinary Level (O/L) subject master directory."""
