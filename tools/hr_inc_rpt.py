"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrIncrementReports() -> list:
    """Retrieves annual salary increment report records for all employees."""


@tool
def fetchHrIncrementReportsByDesignation(designation: int) -> list:
    """Retrieves annual salary increment reports filtered by Designation title."""


@tool
def fetchHrIncrementReportsByIncrementDate(incDate: str) -> list:
    """Retrieves salary increment reports filtered by scheduled increment date (incDate, Format: YYYY-
    MM-DD)."""


@tool
def fetchHrIncrementReportsByIncrementValue(incValue: int) -> list:
    """Retrieves salary increment reports filtered by annual increment monetary step value (incValue in
    the configured currency)."""


@tool
def fetchHrIncrementReportsByDateRange() -> list:
    """Retrieves employee salary increments, annual increment reports, and increment step values whose
    scheduled dates fall within the calendar date range [startDate, endDate]."""
