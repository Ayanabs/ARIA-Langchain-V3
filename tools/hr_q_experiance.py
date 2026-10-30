"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQExperience() -> list:
    """Lists employee work experience records, returning employee identifier, institute name,
    designation, description and application date."""


@tool
def fetchHrQExperienceByEmployeeId(empNo: int) -> list:
    """Lists prior employment history for an employee by identifier, returning institute,
    designation, description and appointment date."""
