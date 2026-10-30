from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQHiEduProjects() -> list:
    """Retrieves postgraduate thesis research project details for employees from GET /api/hr-q-hiedu-projects.
    Database and JSON fields returned per record:
    - id (int): Primary key thesis record ID.
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - ThesisTitle / projectTitle (str): Full title of postgraduate thesis or dissertation project.
    - Field (str): Academic specialization field.
    Maps to GET /api/hr-q-hiedu-projects."""
    return make_request("/api/hr-q-hiedu-projects")
