from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrSalaryDetails() -> list:
    """Retrieves monthly payroll processing records for all employees from GET /api/hr-salary-details.
    Database and JSON fields returned per record:
    - empno / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - basicSalary (float): Basic monthly salary point in the configured currency.
    - netSalary (float): Net salary payment amount.
    - paidDate (str): Payroll disbursement date (Format: YYYY-MM-DD).
    Maps to GET /api/hr-salary-details."""
    return make_request("/api/hr-salary-details")
