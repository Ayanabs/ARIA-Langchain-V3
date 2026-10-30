from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrSalaryTbls() -> list:
    """Retrieves all salary scale structure records across the organisation from GET /api/hr-salary-table.
    Database & JSON fields returned per record:
    - SalaryID (int): Primary key salary record ID.
    - SalaryCode (str) [PRIMARY KEY / FOREIGN KEY]: Unique salary code (e.g. 'SAL001', 'SAL005'). Referenced by 'salarycode' in 'employee', 'hr_official_details', 'hr_designation_tbl'.
    - SalaryGrade (str): Salary grade level (e.g. 'Grade I', 'Grade II', 'Grade III').
    - SalaryScale (str): Full salary scale string specification (e.g. 'Rs. 35,000 - 10x750 - 52,500').
    - SalaryInitVal (float): Initial basic starting salary value in the configured currency.
    - SalaryIncremntYrs (int): Total number of annual increment years/steps.
    - SalaryIncremntAmnt (float): Annual salary increment step amount in the configured currency.
    Maps to GET /api/hr-salary-table."""
    return make_request("/api/hr-salary-table")

@tool
def fetchHrSalaryTblBySalaryCode(salaryCode: str) -> list:
    """Retrieves salary scale details for a specific salary code (salaryCode).
    Arguments & Foreign Key:
    - salaryCode (str) [FOREIGN KEY]: Salary scale code linking to 'salarycode' in 'employee', 'hr_official_details', 'hr_designation_tbl'.
    Returns fields: SalaryID, SalaryCode [FK], SalaryGrade, SalaryScale, SalaryInitVal (basic starting salary), SalaryIncremntYrs, SalaryIncremntAmnt (increment step value).
    Maps to GET /api/hr-salary-table/salary-code/{salaryCode}."""
    return make_request(
        f"/api/hr-salary-table/salary-code/{salaryCode}"
    )

@tool
def fetchHrSalaryTblBySalaryGrade(salaryGrade: str) -> list:
    """Retrieves salary scale records filtered by salary grade (salaryGrade, e.g. 'Grade I', 'Grade II', 'Grade III').
    Returns fields including SalaryCode [FK], SalaryScale, SalaryInitVal, SalaryIncremntAmnt.
    Maps to GET /api/hr-salary-table/salary-grade/{salaryGrade}."""
    cleaned = clean_id(salaryGrade)

    if not cleaned:
        return {
            "error": f"Invalid salary grade format: {salaryGrade}"
        }

    return make_request(
        f"/api/hr-salary-table/salary-grade/{cleaned}"
    )

@tool
def fetchHrSalaryTblBySalaryScale(salaryScale: str) -> list:
    """Retrieves salary scale records matching a full or partial salary scale description string.
    Maps to GET /api/hr-salary-table/salary-scale/{salaryScale}."""
    return make_request(
        f"/api/hr-salary-table/salary-scale/{salaryScale}"
    )

@tool
def fetchHrSalaryTblBySalaryInitVal(salaryInitVal: str) -> list:
    """Retrieves salary scale records filtered by initial basic starting salary value (salaryInitVal in the configured currency).
    Maps to GET /api/hr-salary-table/salary-init-val/{salaryInitVal}."""
    cleaned = clean_id(salaryInitVal)

    if not cleaned:
        return {
            "error": f"Invalid salary initial value format: {salaryInitVal}"
        }

    return make_request(
        f"/api/hr-salary-table/salary-init-val/{cleaned}"
    )

@tool
def fetchHrSalaryTblBySalaryIncrementYears(salaryIncremntYrs: str) -> list:
    """Retrieves salary scale records filtered by the number of annual increment years/steps (salaryIncremntYrs).
    Maps to GET /api/hr-salary-table/salary-increment-years/{salaryIncremntYrs}."""
    cleaned = clean_id(salaryIncremntYrs)

    if not cleaned:
        return {
            "error": f"Invalid salary increment years format: {salaryIncremntYrs}"
        }

    return make_request(
        f"/api/hr-salary-table/salary-increment-years/{cleaned}"
    )

@tool
def fetchHrSalaryTblBySalaryIncrementAmount(salaryIncremntAmnt: str) -> list:
    """Retrieves salary scale records filtered by annual increment step value (salaryIncremntAmnt in the configured currency).
    Maps to GET /api/hr-salary-table/salary-increment-amount/{salaryIncremntAmnt}."""
    cleaned = clean_id(salaryIncremntAmnt)

    if not cleaned:
        return {
            "error": f"Invalid salary increment amount format: {salaryIncremntAmnt}"
        }

    return make_request(
        f"/api/hr-salary-table/salary-increment-amount/{cleaned}"
    )
