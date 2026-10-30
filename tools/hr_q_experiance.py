"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQExperience() -> list:
    """Retrieves all employee prior work experience and employment history records. Each record
    contains: empNo, companyName, designation, startDate, endDate, durationYears,
    responsibilities."""


@tool
def fetchHrQExperienceByEmployeeId(empNo: int) -> list:
    """Retrieves prior employment history and work experience records for an employee by empNo."""
