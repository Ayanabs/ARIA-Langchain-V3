"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrCloseds() -> list:
    """Lists completed project closure records, returning identifier, closure reason, dates,
    invoice, client name and other details."""


@tool
def fetchPrClosedByClId(clId: int) -> list:
    """Lists closed project records selected by closure sequence ID, returning cl id, cl reason
    and cname."""


@tool
def fetchPrClosedByPType(pType: str) -> list:
    """Lists closed project records selected by project type, returning cl id, cl reason and
    cname."""


@tool
def fetchPrClosedByClReason(clReason: str) -> list:
    """Lists closed project records selected by closure reason keyword, returning cl id, cl
    reason and cname."""
