from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpGrades() -> list:
    """Retrieves employee salary grade classification levels from GET /api/emp-grades.
    Database and JSON fields returned per record:
    - GradeCode / grade_code (int) [PRIMARY KEY / FOREIGN KEY]: Salary grade numeric identifier code.
    - Grade / grade_name (str): Salary grade level title (e.g. 'Grade I', 'Grade II', 'Grade III', 'Executive Grade').
    Maps to GET /api/emp-grades."""
    return make_request("/api/emp-grades")
