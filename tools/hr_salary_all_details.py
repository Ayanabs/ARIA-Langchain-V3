from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrSalaryAllDetails() -> list:
    """Retrieves detailed salary slip breakdown calculations for all employees from GET /api/hr-salary-all-details.
    Database and JSON fields returned per record:
    - empno / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - currentSalary / basicSalary (float): Current monthly basic salary point in the configured currency.
    - salaryAfterIncrement (float): Monthly basic salary point after annual increment.
    - incrementValue (float): Annual increment step monetary value in the configured currency.
    - totalPayYears (int): Total years of service completed.
    - remainingYears (int): Remaining years until mandatory retirement.
    - totalAllowances (float): Total monthly gross allowances.
    - totalDeductions (float): Total monthly statutory deductions (EPF 8%, Stamp Duty, etc.).
    - netSalary (float): Take-home net salary payout.
    Maps to GET /api/hr-salary-all-details."""
    return make_request("/api/hr-salary-all-details")

@tool
def fetchHrSalaryAllDetailsByEmpNo(empNo: str) -> dict:
    """Retrieves detailed salary breakdown calculations for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: empno [FK], currentSalary, salaryAfterIncrement, incrementValue, totalPayYears, remainingYears, basicSalary, totalAllowances, totalDeductions, netSalary.
    Maps to GET /api/hr-salary-all-details/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    return make_request(f"/api/hr-salary-all-details/{cleaned}")
