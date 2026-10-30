"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrCloseds() -> list:
    """Retrieves completed and closed PR project records."""


@tool
def fetchPrClosedByClId(clId: int) -> list:
    """Retrieves closed project records by closure sequence ID (clId)."""


@tool
def fetchPrClosedByPType(pType: str) -> list:
    """Retrieves closed project records filtered by project type classification (pType)."""


@tool
def fetchPrClosedByClReason(clReason: str) -> list:
    """Retrieves closed project records filtered by closure reason keyword."""
