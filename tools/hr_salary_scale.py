from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrSalaryScales() -> list:
    """Retrieves salary scale definition master records from GET /api/hr-salary-scales.
    Database and JSON fields returned per record:
    - scale_id / id (int) [PRIMARY KEY / FOREIGN KEY]: Salary scale identifier code.
    - scale_name / scale_code (str): Salary scale code (e.g. 'SAL001', 'SAL005').
    - scale_description (str): Full salary scale string specification (e.g. 'Rs. 35,000 - 10x750 - 52,500').
    Maps to GET /api/hr-salary-scales."""
    return make_request("/api/hr-salary-scales")
