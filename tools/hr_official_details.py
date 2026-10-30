"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrOfficialDetails() -> list:
    """Retrieves official appointment and career details for all employees."""


@tool
def fetchHrOfficialDetailsByEmpNo(empNo: int) -> dict:
    """Retrieves official appointment and career record for a specific employee by empNo."""


@tool
def fetchHrOfficialDetailsByDesignation(desigCode: int) -> list:
    """Retrieves official career details for all employees holding a specific designation."""


@tool
def fetchHrOfficialDetailsByCategory(category: str) -> list:
    """Retrieves official career details for all employees belonging to a specific staff category."""


@tool
def fetchHrOfficialDetailsByEmployeeStatus(empActive: str) -> list:
    """Retrieves official career records for ALL employees filtered by employment status code."""
