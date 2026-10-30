from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpCleanings() -> list:
    """Retrieves duty assignments for cleaning and maintenance staff from GET /api/emp-cleanings.
    Database and JSON fields returned per record:
    - id (int): Primary key row identifier.
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - Location (str): Assigned building floor, section, or office area location.
    - Shift (str): Assigned duty shift ('Morning', 'Evening').
    Maps to GET /api/emp-cleanings."""
    return make_request("/api/emp-cleanings")
