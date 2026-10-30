"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchPrChangeHistoryBySerialNo(serialNo: int) -> list:
    """Lists change history records selected by serial number, returning id, capital, recurrent
    and income."""


@tool
def fetchPrChangeHistoryByNewApCode(newApCode: str) -> list:
    """Lists change history records selected by new AP code, returning ID, serial number,
    capital amount and recurrent amount."""


@tool
def fetchPrChangeHistoryByApCodeYear(apCodeYear: int) -> list:
    """Lists change history records selected by AP code year, returning ID, serial number,
    capital amount and recurrent amount."""
