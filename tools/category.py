"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllCategories() -> list:
    """Retrieves all staff work category and shift schedule records."""


@tool
def fetchCategoryByCategory(category: str) -> dict:
    """Retrieves staff work category schedule details by category description or group name."""
