from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrSalaryScaleDetails() -> list:
    """Retrieves detailed salary scale increment step breakdowns from GET /api/hr-salary-scale-details.
    Database and JSON fields returned per record:
    - id (int): Primary key step breakdown ID.
    - scale_id (int) [FOREIGN KEY]: Foreign key linking to 'scale_id' in 'hr_salary_scales'.
    - step_number (int): Annual increment step index (1, 2, 3, ...).
    - salary_point (float): Salary monetary value at step index in the configured currency.
    Maps to GET /api/hr-salary-scale-details."""
    return make_request("/api/hr-salary-scale-details")
