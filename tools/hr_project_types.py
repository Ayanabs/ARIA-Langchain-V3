"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrProjectTypes() -> list:
    """Retrieves HR project type classification categories."""


@tool
def fetchHrProjectTypesByShortDescription(ptShortDes: str) -> list:
    """Retrieves project types filtered by short acronym description (ptShortDes)."""


@tool
def fetchHrProjectTypesByDescription(ptDescription: str) -> list:
    """Retrieves project types filtered by full description string (ptDescription)."""
