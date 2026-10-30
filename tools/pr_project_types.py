"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjectTypes() -> list:
    """Lists all PR project types, returning pt code, pt short des and pt description."""


@tool
def fetchPrProjectTypeByCode(ptCode: int) -> dict:
    """Gets a project type record selected by its code, returning the code, short description
    and full description."""


@tool
def fetchPrProjectTypesByShortDescription(ptShortDes: str) -> list:
    """Lists project type records selected by their short description, returning the code, short
    description and full description."""


@tool
def fetchPrProjectTypesByDescription(ptDescription: str) -> list:
    """Lists project type records selected by their full description, returning the code, short
    description and full description."""
