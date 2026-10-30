"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQOL() -> list:
    """Retrieves G.C.E. Ordinary Level (O/L) examination results for all employees."""


@tool
def fetchHrQOLByEmployeeNo(empNo: str) -> list:
    """Retrieves G.C.E. Ordinary Level (O/L) examination subject results for an employee by Employee
    Number (empNo)."""


@tool
def fetchHrQOLByOLIndex(oLIndex: str) -> list:
    """Retrieves G.C.E. O/L exam records by Candidate Index Number (oLIndex)."""


@tool
def fetchHrQOLByOLSubNo(oLSubNo: str) -> list:
    """Retrieves G.C.E. O/L exam records by Subject Number (oLSubNo )."""


@tool
def fetchHrQOLByOLSubGrade(oLSubGrade: str) -> list:
    """Retrieves G.C.E. O/L exam records by Subject Grade."""


@tool
def fetchHrQOLByOLYear(oLYear: int) -> list:
    """Retrieves G.C.E. O/L exam records by Examination Year."""
