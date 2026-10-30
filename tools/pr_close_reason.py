"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrCloseReasons() -> list:
    """Lists master justification reasons for project closure, returning identifier, project
    type, reason code and order reference."""


@tool
def fetchPrCloseReasonsByPrType(prType: str) -> list:
    """Lists closure reasons selected by project type, returning pr type, cl reason and order
    re."""


@tool
def fetchPrCloseReasonsByReason(clReason: str) -> list:
    """Lists closure reasons selected by reason keyword, returning pr type, cl reason and order
    re."""
