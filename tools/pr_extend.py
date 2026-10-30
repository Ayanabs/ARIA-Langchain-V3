"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrExtends() -> list:
    """Retrieves all PR extension records."""


@tool
def fetchPrExtendsByExId(exId: int) -> list:
    """Retrieves PR extension records filtered by extension ID (ex_id)."""


@tool
def fetchPrExtendsByExtendedDate(extendedDate: str) -> list:
    """Retrieves PR extension records filtered by extended date (YYYY-MM-DD)."""


@tool
def fetchPrExtendsByEdate(edate: str) -> list:
    """Retrieves PR extension records filtered by edate (YYYY-MM-DD)."""
