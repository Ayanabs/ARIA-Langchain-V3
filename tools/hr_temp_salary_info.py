from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id


@tool
def fetchAllHrTempSalaryInfo() -> list:
    """Retrieves temporary salary calculation statements for all employees from GET /api/hr-temp-salary-info.
    Database & JSON fields returned per record:
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - Order (int): Order/sequence number.
    - PreparedDate (str): Date statement was generated/prepared (Format: YYYY-MM-DD).
    - NameFull (str): Full name of employee.
    - Designation (str) [FOREIGN KEY]: Designation job title (linking to 'hr_designation_tbl').
    - SalScale / salaryScale (str) [FOREIGN KEY]: Salary scale code/description (linking to 'hr_salary_tbl').
    - PresentSal / basicSalary (float): Current monthly basic salary point in the configured currency.
    - IncDate (str): Next annual increment date (Format: YYYY-MM-DD).
    - IncValue (float): Annual increment step monetary value in the configured currency.
    - FinalSal / netSalary (float): Net total salary after increment step and allowances.
    Maps to GET /api/hr-temp-salary-info."""
    return make_request("/api/hr-temp-salary-info")


@tool
def fetchHrTempSalaryInfoByEmpNo(empNo: str) -> dict:
    """Retrieves temporary salary calculation statement for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: EmpNo [FK], PreparedDate, NameFull, Designation [FK], SalScale [FK], PresentSal (basic salary point), IncDate, IncValue, FinalSal (net salary).
    Maps to GET /api/hr-temp-salary-info/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {
            "error": f"Invalid employee number format: {empNo}"
        }

    return make_request(
        f"/api/hr-temp-salary-info/{cleaned}"
    )


@tool
def fetchHrTempSalaryInfoByDesignation(designation: str) -> list:
    """Retrieves temporary salary statements filtered by Designation job title.
    Arguments & Foreign Key:
    - designation (str) [FOREIGN KEY]: Designation title linking to 'hr_designation_tbl'.
    Maps to GET /api/hr-temp-salary-info/designation/{designation}."""
    return make_request(
        f"/api/hr-temp-salary-info/designation/{designation}"
    )


@tool
def fetchHrTempSalaryInfoBySalaryScale(salScale: str) -> list:
    """Retrieves temporary salary statements filtered by Salary Scale specification/code (salScale).
    Arguments & Foreign Key:
    - salScale (str) [FOREIGN KEY]: Salary scale code linking to 'hr_salary_tbl'.
    Maps to GET /api/hr-temp-salary-info/salary-scale/{salScale}."""
    return make_request(
        f"/api/hr-temp-salary-info/salary-scale/{salScale}"
    )


@tool
def fetchHrTempSalaryInfoByName(nameFull: str) -> list:
    """Retrieves temporary salary statements matching an employee's full name (nameFull).
    Maps to GET /api/hr-temp-salary-info/name/{nameFull}."""
    return make_request(
        f"/api/hr-temp-salary-info/name/{nameFull}"
    )


@tool
def fetchHrTempSalaryInfoByPreparedDate(preparedDate: str) -> list:
    """Retrieves temporary salary statements filtered by preparation date (preparedDate, Format: YYYY-MM-DD).
    Maps to GET /api/hr-temp-salary-info/date/{preparedDate}."""
    return make_request(
        f"/api/hr-temp-salary-info/date/{preparedDate}"
    )