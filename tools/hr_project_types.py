"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrProjectTypes() -> list:
    """Lists HR project type classifications, returning the code, short description and full
    description for each project category."""


@tool
def fetchHrProjectTypesByShortDescription(ptShortDes: str) -> list:
    """Lists project types filtered by short description, returning code, short description and
    full description."""


@tool
def fetchHrProjectTypesByDescription(ptDescription: str) -> list:
    """Lists project types filtered by full description, returning code, short description and
    full description."""
