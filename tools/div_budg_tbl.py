"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllDivBudgets() -> list:
    """Lists all division budget records, returning the budget code, division code, budget year,
    and requested amount."""


@tool
def fetchDivBudgetsByDivisionCode(divCode: int) -> list:
    """Lists budget records for a division selected by its code, returning the year, requested
    amount, and approved amount."""


@tool
def fetchDivBudgetsByBudgetYear(budgYear: str) -> list:
    """Lists division budget allocations for a specific financial budget year, returning divb
    code, div code, budg code, budg year, user descrip, req amount, appr amount, req confirm,
    app confirm and the amount."""
