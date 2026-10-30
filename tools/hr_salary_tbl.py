"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrSalaryTbls() -> list:
    """Retrieves all salary scale structure records across the organisation."""


@tool
def fetchHrSalaryTblBySalaryCode(salaryCode: str) -> list:
    """Retrieves salary scale details for a specific salary code (salaryCode)."""


@tool
def fetchHrSalaryTblBySalaryGrade(salaryGrade: int) -> list:
    """Retrieves salary scale records filtered by salary grade."""


@tool
def fetchHrSalaryTblBySalaryScale(salaryScale: str) -> list:
    """Retrieves salary scale records matching a full or partial salary scale description string."""


@tool
def fetchHrSalaryTblBySalaryInitVal(salaryInitVal: int) -> list:
    """Retrieves salary scale records filtered by initial basic starting salary value (salaryInitVal in
    the configured currency)."""


@tool
def fetchHrSalaryTblBySalaryIncrementYears(salaryIncremntYrs: int) -> list:
    """Retrieves salary scale records filtered by the number of annual increment years/steps
    (salaryIncremntYrs)."""


@tool
def fetchHrSalaryTblBySalaryIncrementAmount(salaryIncremntAmnt: int) -> list:
    """Retrieves salary scale records filtered by annual increment step value (salaryIncremntAmnt in
    the configured currency)."""
