"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQALSubjects() -> list:
    """Lists A/L subject directory records, returning subject code and subject name."""


@tool
def fetchHrQALSubjectsBySubjectName(subName: str) -> list:
    """Lists G.C.E. A/L subject details by subject name, returning subject code and subject
    name."""
