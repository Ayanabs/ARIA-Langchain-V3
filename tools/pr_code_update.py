"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrCodeUpdates() -> list:
    """Lists historical project code remapping logs, returning recurrence flag, capital status,
    expected income, old year and type."""


@tool
def fetchPrCodeUpdatesByPRCode(pRCode: str) -> list:
    """Lists project code updates selected by project code, returning recurrent, capital and
    expected income."""


@tool
def fetchPrCodeUpdatesByAcPlCode(aCPlCode: str) -> list:
    """Lists project code updates selected by accounting plan code, returning recurrent, capital
    and expected income."""
