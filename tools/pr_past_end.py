"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrPastEnds() -> list:
    """Retrieves all PR past end records."""


@tool
def fetchPrPastEndsByPrCode(prCode: str) -> list:
    """Retrieves PR past end records filtered by PR code."""


@tool
def fetchPrPastEndsByEndDate(endDate: str) -> list:
    """Retrieves PR past end records filtered by end date (YYYY-MM-DD)."""
