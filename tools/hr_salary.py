from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrSalaries() -> list:
    """Retrieves salary scale summary records from GET /api/hr-salaries.
    Database and JSON fields returned per record:
    - id (int): Primary key record ID.
    - salary_scale / sal_scale (str) [PRIMARY KEY / FOREIGN KEY]: Salary scale code (e.g. 'SAL001', 'SAL005').
    - basic_salary / init_val (float): Initial basic starting salary point in the configured currency.
    - inc_value (float): Annual increment step monetary value in the configured currency.
    Maps to GET /api/hr-salaries."""
    return make_request("/api/hr-salaries")
