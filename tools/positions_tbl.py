"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPositions() -> list:
    """Retrieves all position history records across the organisation."""


@tool
def fetchPositionByEmpNo(empNo: int) -> dict:
    """Retrieves position history and promotion records for an employee by empNo."""


@tool
def fetchPositionsByDivisionCode(divisionCode: int) -> list:
    """Retrieves position history records for all employees in a specific division."""


@tool
def fetchPositionsByDesigCode(desigCode: int) -> list:
    """Retrieves position history records for all employees holding a specific designation."""


@tool
def fetchPositionsByCategoryCode(categoryCode: int) -> list:
    """Retrieves position history records for all employees belonging to a specific category."""


@tool
def fetchPositionsByPromoDate(promoDt: str) -> list:
    """Retrieves position and promotion records filtered by promotion date (Format: YYYY-MM-DD). Use
    when searching for employees promoted on a specific date or year."""
