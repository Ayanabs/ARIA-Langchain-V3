"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQAL() -> list:
    """Lists A/L examination result records, returning employee number, exam year, subject name
    and subject grade."""


@tool
def fetchHrQALByEmployeeNo(empNo: str) -> list:
    """Lists A/L examination results for an employee by employee number, returning examination
    year, subject name and grade."""


@tool
def fetchHrQALByALIndex(aLIndex: str) -> list:
    """Lists A/L examination records filtered by index number, returning employee number,
    examination year, subject name and grade."""


@tool
def fetchHrQALByALSubNo(aLSubNo: str) -> list:
    """Lists A/L examination records filtered by subject code, returning employee number,
    examination year, subject name and grade."""


@tool
def fetchHrQALByALSubGrade(aLSubGrade: str) -> list:
    """Lists A/L examination records filtered by subject grade, returning employee number,
    examination year, subject name and grade."""


@tool
def fetchHrQALByALYear(aLYear: int) -> list:
    """Lists A/L examination records filtered by examination year, returning employee number,
    subject code, subject name and grade."""
