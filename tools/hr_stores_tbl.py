"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrStores() -> list:
    """Retrieves HR store inventory item allocations."""


@tool
def fetchHrStoresByStCode(stCode: str) -> list:
    """Retrieves store inventory items filtered by store item code (stCode)."""


@tool
def fetchHrStoresBySerialNo(serialNo: int) -> list:
    """Retrieves store inventory items filtered by asset serial number (serialNo)."""
