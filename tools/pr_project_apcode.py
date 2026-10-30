"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjectApcodes() -> list:
    """Retrieves all PR project AP codes."""


@tool
def fetchPrProjectApcodesByApcode(apcode: str) -> list:
    """Retrieves PR project AP codes filtered by apcode string."""


@tool
def fetchPrProjectApcodesByYear(year: int) -> list:
    """Retrieves PR project AP codes filtered by year."""
