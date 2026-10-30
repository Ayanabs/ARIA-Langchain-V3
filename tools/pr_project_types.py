"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjectTypes() -> list:
    """Retrieves all PR project types."""


@tool
def fetchPrProjectTypeByCode(ptCode: int) -> dict:
    """Retrieves PR project type definition by primary key project type code (ptCode )."""


@tool
def fetchPrProjectTypesByShortDescription(ptShortDes: str) -> list:
    """Retrieves PR project types filtered by short description."""


@tool
def fetchPrProjectTypesByDescription(ptDescription: str) -> list:
    """Retrieves PR project types filtered by full description."""
