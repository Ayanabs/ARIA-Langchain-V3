"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQHiEdus() -> list:
    """Lists higher education qualification records, returning employee number, diploma, degree,
    certificate, masters, PhD and professional qualification fields."""


@tool
def fetchHrQHieduByEmpNo(empNo: str) -> list:
    """Lists higher education qualifications for an employee by number, returning diploma,
    degree, masters and PhD fields."""
