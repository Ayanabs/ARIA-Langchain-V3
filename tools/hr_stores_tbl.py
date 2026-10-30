"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrStores() -> list:
    """Lists HR store inventory allocations including store identifier, serial number, and store
    code."""


@tool
def fetchHrStoresByStCode(stCode: str) -> list:
    """Lists store inventory items filtered by store code, returning the item ID, serial number
    and store code."""


@tool
def fetchHrStoresBySerialNo(serialNo: int) -> list:
    """Lists store inventory items filtered by serial number, returning the item ID, serial
    number and store code."""
