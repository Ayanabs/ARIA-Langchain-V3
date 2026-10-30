"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrQAL() -> list:
    """Retrieves G.C.E. Advanced Level (A/L) examination results for all employees."""


@tool
def fetchHrQALByEmployeeNo(empNo: str) -> list:
    """Retrieves G.C.E. Advanced Level (A/L) examination subject results for an employee by Employee
    Number (empNo)."""


@tool
def fetchHrQALByALIndex(aLIndex: str) -> list:
    """Retrieves A/L examination records filtered by G.C.E. Advanced Level Examination Index Number
    (aLIndex)."""


@tool
def fetchHrQALByALSubNo(aLSubNo: str) -> list:
    """Retrieves A/L examination records filtered by Subject Number/Code (aLSubNo)."""


@tool
def fetchHrQALByALSubGrade(aLSubGrade: str) -> list:
    """Retrieves A/L examination records filtered by Subject Grade."""


@tool
def fetchHrQALByALYear(aLYear: int) -> list:
    """Retrieves A/L examination records filtered by examination year."""
