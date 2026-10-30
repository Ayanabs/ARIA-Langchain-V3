"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchPrChangeHistoryBySerialNo(serialNo: int) -> list:
    """Retrieves change history records for a project by primary key serial sequence number (serialNo
    )."""


@tool
def fetchPrChangeHistoryByNewApCode(newApCode: str) -> list:
    """Retrieves change history records filtered by updated AP code (newApCode)."""


@tool
def fetchPrChangeHistoryByApCodeYear(apCodeYear: int) -> list:
    """Retrieves change history records filtered by AP code year (apCodeYear)."""
