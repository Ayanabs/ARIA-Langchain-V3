"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjectApcodes() -> list:
    """Lists all PR project ap codes, returning id, pr code, year and ap code."""


@tool
def fetchPrProjectApcodesByApcode(apcode: str) -> list:
    """Lists project AP codes filtered by an AP code string, returning project code, year, and
    AP code."""


@tool
def fetchPrProjectApcodesByYear(year: int) -> list:
    """Lists project AP codes filtered by a year, returning project code, year, and AP code."""
