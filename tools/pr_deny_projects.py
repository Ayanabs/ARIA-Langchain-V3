from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrDenyProjects() -> list:
    """Retrieves denied PR project proposal records from GET /api/pr-deny-projects.
    Database and JSON fields returned per record:
    - id (int): Primary key denied project record ID.
    - pr_code / code (str) [FOREIGN KEY]: PR project code (linking to 'code' in 'pr_projects').
    - deny_reason (str): Justification for proposal denial.
    - deny_date (str): Date proposal was rejected (Format: YYYY-MM-DD).
    Maps to GET /api/pr-deny-projects."""
    return make_request("/api/pr-deny-projects")

@tool
def fetchPrDenyProjectsByPCode(pCode: str) -> list:
    """Retrieves denial records for a specific project by Project Code (pCode [FK]).
    Maps to GET /api/pr-deny-projects/p-code/{pCode}."""
    cleaned = clean_id(pCode)
    if not cleaned:
        return {"error": "Invalid project code format"}
    return make_request(f"/api/pr-deny-projects/p-code/{cleaned}")

@tool
def fetchPrDenyProjectsByReason(reason: str) -> list:
    """Retrieves denied projects filtered by denial reason keyword.
    Maps to GET /api/pr-deny-projects/reason/{reason}."""
    if not reason or not str(reason).strip():
        return {"error": "Reason cannot be empty"}
    return make_request(f"/api/pr-deny-projects/reason/{str(reason).strip()}")
