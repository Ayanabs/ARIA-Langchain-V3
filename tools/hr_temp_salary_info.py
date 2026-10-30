"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrTempSalaryInfo() -> list:
    """Retrieves temporary salary calculation statements for all employees."""


@tool
def fetchHrTempSalaryInfoByEmpNo(empNo: int) -> list:
    """Retrieves temporary salary calculation statement for a specific employee by Employee Number
    (empNo)."""


@tool
def fetchHrTempSalaryInfoByDesignation(designation: str) -> list:
    """Retrieves temporary salary statements filtered by Designation job title."""


@tool
def fetchHrTempSalaryInfoBySalaryScale(salScale: str) -> list:
    """Retrieves temporary salary statements filtered by Salary Scale specification/code (salScale)."""


@tool
def fetchHrTempSalaryInfoByName(nameFull: str) -> list:
    """Retrieves temporary salary statements matching an employee's full name (nameFull)."""


@tool
def fetchHrTempSalaryInfoByPreparedDate(preparedDate: str) -> list:
    """Retrieves temporary salary statements filtered by preparation date (preparedDate, Format: YYYY-
    MM-DD)."""
