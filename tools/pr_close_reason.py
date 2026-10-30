"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrCloseReasons() -> list:
    """Retrieves master justification reasons for project closure."""


@tool
def fetchPrCloseReasonsByPrType(prType: str) -> list:
    """Retrieves closure reasons filtered by project type classification (prType)."""


@tool
def fetchPrCloseReasonsByReason(clReason: str) -> list:
    """Retrieves closure reasons filtered by reason description keyword (clReason)."""
