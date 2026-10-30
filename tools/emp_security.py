"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmpSecurities() -> list:
    """Retrieves security staff roster and gate post duty assignments."""


@tool
def fetchEmpSecuritiesByRank(rank: str) -> list:
    """Retrieves security staff records with a given rank."""


@tool
def fetchEmpSecuritiesByStatus(status: int) -> list:
    """Retrieves security staff records with a given status code."""
