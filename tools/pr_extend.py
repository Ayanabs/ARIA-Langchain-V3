"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrExtends() -> list:
    """Lists project extension records, returning identifier, extension identifier, extended
    date and end date."""


@tool
def fetchPrExtendsByExId(exId: int) -> list:
    """Lists extension records filtered by an extension identifier, returning id, extension
    identifier, extended date, and entry date."""


@tool
def fetchPrExtendsByExtendedDate(extendedDate: str) -> list:
    """Lists extension records filtered by an extended date, returning id, extension identifier,
    extended date, and entry date."""


@tool
def fetchPrExtendsByEdate(edate: str) -> list:
    """Lists extension records filtered by an entry date, returning id, extension identifier,
    extended date, and entry date."""
