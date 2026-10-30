"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrStoresTbl() -> list:
    """Retrieves all PR stores records."""


@tool
def fetchPrStoresTblByStCode(stCode: str) -> list:
    """Retrieves PR stores records filtered by store code."""


@tool
def fetchPrStoresTblBySerialNo(serialNo: int) -> list:
    """Retrieves PR stores records filtered by serial number."""
