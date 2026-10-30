"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrPastEnds() -> list:
    """Lists all PR records past their end date, returning id, pr code, end date, recurrent and
    capital."""


@tool
def fetchPrPastEndsByPrCode(prCode: str) -> list:
    """Lists past end records filtered by a project code, returning project code, end date,
    recurrent status, and capital."""


@tool
def fetchPrPastEndsByEndDate(endDate: str) -> list:
    """Lists past end records filtered by an end date, returning project code, end date,
    recurrent status, and capital."""
