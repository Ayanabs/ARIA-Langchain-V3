"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrDenyClosedprjs() -> list:
    """Lists rejected project closure request logs, returning close reason and project code."""


@tool
def fetchPrDenyClosedprjByPCode(pCode: str) -> dict:
    """Gets a rejected project closure record selected by project code, returning close reason
    and pcode."""


@tool
def fetchPrDenyClosedprjByCloseReason(closeReason: str) -> list:
    """Lists denied project closures selected by close reason keyword, returning close reason
    and pcode."""
