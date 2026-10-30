"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrHigherEduDetails() -> list:
    """Retrieves higher education qualification records for all employees."""


@tool
def fetchHrHighereduDetailsByEmployee(empNo: int) -> list:
    """Retrieves higher education degrees, diplomas, postgraduate, and doctorate qualifications for an
    employee by Employee Number (empNo)."""


@tool
def fetchHrHighereduDetailsBySubEduType(subEduType: int) -> list:
    """Retrieves higher education records filtered by sub-education category."""


@tool
def fetchHrHighereduDetailsByHigherEduLevel(higherEduLevel: int) -> list:
    """Retrieves higher education records filtered by academic level."""
