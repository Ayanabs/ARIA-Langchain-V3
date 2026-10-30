"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQALSubjects() -> list:
    """Retrieves G.C.E. Advanced Level (A/L) subject master directory."""


@tool
def fetchHrQALSubjectsBySubjectName(subName: str) -> list:
    """Retrieves G.C.E. A/L subject details by subject name."""
