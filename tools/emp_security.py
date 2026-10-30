"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpSecurities() -> list:
    """Lists security staff roster records, returning employee ID, name, ID number, rank, and
    status."""


@tool
def fetchEmpSecuritiesByRank(rank: str) -> list:
    """Lists security staff records selected by their rank, returning the name, identification
    number, and current status."""


@tool
def fetchEmpSecuritiesByStatus(status: int) -> list:
    """Lists security staff records selected by a specific status code, returning the name,
    identification number, and rank."""
