"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrDenyClosedprjs() -> list:
    """Retrieves rejected project closure request logs."""


@tool
def fetchPrDenyClosedprjByPCode(pCode: str) -> dict:
    """Retrieves rejected project closure request log for a specific project by Project Code (pCode )."""


@tool
def fetchPrDenyClosedprjByCloseReason(closeReason: str) -> list:
    """Retrieves denied project closures filtered by close reason keyword."""
