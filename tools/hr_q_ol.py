"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQOL() -> list:
    """Lists O/L examination result records, returning employee number, exam year, subject name
    and subject grade."""


@tool
def fetchHrQOLByEmployeeNo(empNo: str) -> list:
    """Lists G.C.E. O/L examination results for an employee by number, returning subject name,
    year and grade."""


@tool
def fetchHrQOLByOLIndex(oLIndex: str) -> list:
    """Lists G.C.E. O/L exam records selected by candidate index number, returning employee
    number, subject name, grade and year."""


@tool
def fetchHrQOLByOLSubNo(oLSubNo: str) -> list:
    """Lists G.C.E. O/L exam records selected by subject number, returning employee number,
    subject name, grade and year."""


@tool
def fetchHrQOLByOLSubGrade(oLSubGrade: str) -> list:
    """Lists G.C.E. O/L exam records selected by subject grade, returning employee number,
    subject name, index and year."""


@tool
def fetchHrQOLByOLYear(oLYear: int) -> list:
    """Lists G.C.E. O/L exam records selected by examination year, returning employee number,
    subject name, grade and index."""
