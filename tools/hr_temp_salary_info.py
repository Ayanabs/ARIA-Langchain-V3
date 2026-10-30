"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrTempSalaryInfo() -> list:
    """Lists temporary salary statements including employee number, full name, designation,
    present salary, and final salary."""


@tool
def fetchHrTempSalaryInfoByEmpNo(empNo: int) -> list:
    """Lists temporary salary statements for an employee number, returning the employee number,
    full name, designation, current salary and final salary."""


@tool
def fetchHrTempSalaryInfoByDesignation(designation: str) -> list:
    """Lists temporary salary statements filtered by job title, returning the employee number,
    full name, designation, current salary and final salary."""


@tool
def fetchHrTempSalaryInfoBySalaryScale(salScale: str) -> list:
    """Lists temporary salary statements filtered by salary scale code, returning the employee
    number, full name, designation, current salary and final salary."""


@tool
def fetchHrTempSalaryInfoByName(nameFull: str) -> list:
    """Lists temporary salary statements matching a full name, returning the employee number,
    full name, designation, current salary and final salary."""


@tool
def fetchHrTempSalaryInfoByPreparedDate(preparedDate: str) -> list:
    """Lists temporary salary statements filtered by preparation date, returning the employee
    number, full name, designation, current salary and final salary."""
