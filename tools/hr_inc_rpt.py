"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrIncrementReports() -> list:
    """Lists annual salary increment reports, returning the name, designation, salary scale,
    point, date, value and basic salary."""


@tool
def fetchHrIncrementReportsByDesignation(designation: int) -> list:
    """Lists salary increment records filtered by a specific designation code, returning name,
    designation, present salary point, and increment value."""


@tool
def fetchHrIncrementReportsByIncrementDate(incDate: str) -> list:
    """Lists salary increment records filtered by a specific scheduled increment date string,
    returning name, designation, present salary point, and increment value."""


@tool
def fetchHrIncrementReportsByIncrementValue(incValue: int) -> list:
    """Lists salary increment records filtered by a specific monetary increment step value,
    returning name, designation, present salary point, and increment value."""


@tool
def fetchHrIncrementReportsByDateRange() -> list:
    """Lists salary increment records for employees whose scheduled dates fall within a
    specified calendar date range, returning name, designation, present salary point, and
    increment value."""
