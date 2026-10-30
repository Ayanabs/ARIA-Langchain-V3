"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDivBudgets() -> list:
    """Retrieves all division budget records across the organisation."""


@tool
def fetchDivBudgetsByDivisionCode(divCode: int) -> list:
    """Retrieves annual budget allocations for a specific division using divCode."""


@tool
def fetchDivBudgetsByBudgetYear(budgYear: str) -> list:
    """Retrieves division budget allocations for a specific financial budget year."""
