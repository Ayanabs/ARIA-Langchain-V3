"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrOfficialDetails() -> list:
    """Lists official appointment details for employees, returning the employee number,
    appointment date, division code, category and designation code."""


@tool
def fetchHrOfficialDetailsByEmpNo(empNo: int) -> dict:
    """Gets official appointment and career record for a specific employee identified by an
    employee number, returning employee number, appointment date, division code, and category."""


@tool
def fetchHrOfficialDetailsByDesignation(desigCode: int) -> list:
    """Lists official career details for employees holding a specific designation code,
    returning employee number, appointment date, division code, and category."""


@tool
def fetchHrOfficialDetailsByCategory(category: str) -> list:
    """Lists official career details for employees belonging to a specific staff category
    string, returning employee number, appointment date, division code, and category."""


@tool
def fetchHrOfficialDetailsByEmployeeStatus(empActive: str) -> list:
    """Lists official career records for all employees filtered by a specific employment status
    string, returning employee number, appointment date, division code, and category."""
