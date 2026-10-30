"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrHigherEduDetails() -> list:
    """Lists higher education qualification records for employees, returning the employee
    number, education type, level and description."""


@tool
def fetchHrHighereduDetailsByEmployee(empNo: int) -> list:
    """Lists higher education records selected by employee number, returning sub edu type,
    higher edu level, description, and emp no."""


@tool
def fetchHrHighereduDetailsBySubEduType(subEduType: int) -> list:
    """Lists higher education records selected by sub-education type, returning sub edu type,
    higher edu level, description, and emp no."""


@tool
def fetchHrHighereduDetailsByHigherEduLevel(higherEduLevel: int) -> list:
    """Lists higher education records selected by academic level, returning sub edu type, higher
    edu level, description, and emp no."""
