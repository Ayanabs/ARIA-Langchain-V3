"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrStoresTbl() -> list:
    """Lists all PR stores records, returning st id, serial no and st code."""


@tool
def fetchPrStoresTblByStCode(stCode: str) -> list:
    """Lists store records selected by store code, returning store identifier, serial number,
    and store code."""


@tool
def fetchPrStoresTblBySerialNo(serialNo: int) -> list:
    """Lists store records selected by serial number, returning store identifier, serial number,
    and store code."""
