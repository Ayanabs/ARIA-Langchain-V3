"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllCategories() -> list:
    """Lists all staff work categories and shift schedules, returning the category code,
    category name, in time, and out time."""


@tool
def fetchCategoryByCategory(category: str) -> dict:
    """Gets staff work category schedule details by category, returning categorycode, category,
    intime, outtimeh, outtimem, adjesttime, latetime and sp latetime."""
