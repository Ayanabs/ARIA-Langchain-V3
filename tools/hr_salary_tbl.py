"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryTbls() -> list:
    """Lists salary scale structures including salary code, grade, scale, initial value,
    increment years, and amount."""


@tool
def fetchHrSalaryTblBySalaryCode(salaryCode: str) -> list:
    """Lists salary scale records selected by salary code, returning salary grade, scale,
    initial value and increment amount."""


@tool
def fetchHrSalaryTblBySalaryGrade(salaryGrade: int) -> list:
    """Lists salary scale records selected by salary grade, returning salary code, scale,
    initial value and increment years."""


@tool
def fetchHrSalaryTblBySalaryScale(salaryScale: str) -> list:
    """Lists salary scale records matching a description string, returning the ID, code, grade,
    initial value, increment years and amount."""


@tool
def fetchHrSalaryTblBySalaryInitVal(salaryInitVal: int) -> list:
    """Lists salary scale records selected by initial basic starting salary value, returning
    salary code, grade, scale and increment years."""


@tool
def fetchHrSalaryTblBySalaryIncrementYears(salaryIncremntYrs: int) -> list:
    """Lists salary scale records selected by number of increment years, returning salary code,
    grade, scale and increment amount."""


@tool
def fetchHrSalaryTblBySalaryIncrementAmount(salaryIncremntAmnt: int) -> list:
    """Lists salary scale records selected by annual increment amount, returning salary code,
    grade, scale and initial value."""
