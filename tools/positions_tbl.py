"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPositions() -> list:
    """Lists position history records across the organisation, returning employee number,
    promotion date, division, designation and category codes."""


@tool
def fetchPositionByEmpNo(empNo: int) -> dict:
    """Gets position history record selected by employee number, returning employee number,
    promotion date, division code and designation code."""


@tool
def fetchPositionsByDivisionCode(divisionCode: int) -> list:
    """Lists position records selected by division code, returning employee number, promotion
    date, designation code and category code."""


@tool
def fetchPositionsByDesigCode(desigCode: int) -> list:
    """Lists position records selected by designation code, returning employee number, promotion
    date, division code and category code."""


@tool
def fetchPositionsByCategoryCode(categoryCode: int) -> list:
    """Lists position records selected by category code, returning employee number, promotion
    date, division code and designation code."""


@tool
def fetchPositionsByPromoDate(promoDt: str) -> list:
    """Lists position records selected by promotion date, returning employee number, promotion
    date, division code and designation code."""
