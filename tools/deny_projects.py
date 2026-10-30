from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllDenyProjects() -> list:
    """Retrieves rejected or denied project proposal records from GET /api/deny-projects.
    Database and JSON fields returned per record:
    - id (int): Primary key denied project record ID.
    - project_code / code (str) [FOREIGN KEY]: Project code (linking to 'code' in 'hr_projects' / 'pr_projects').
    - deny_reason (str): Official justification or reason for proposal rejection.
    - deny_date (str): Date of proposal rejection (Format: YYYY-MM-DD).
    Maps to GET /api/deny-projects."""
    return make_request("/api/deny-projects")
