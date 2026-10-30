"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrCodeUpdates() -> list:
    """Retrieves historical project code remapping logs."""


@tool
def fetchPrCodeUpdatesByPRCode(pRCode: str) -> list:
    """Retrieves project code update records for a specific project code (pRCode )."""


@tool
def fetchPrCodeUpdatesByAcPlCode(aCPlCode: str) -> list:
    """Retrieves project code update records filtered by accounting plan code (aCPlCode)."""
