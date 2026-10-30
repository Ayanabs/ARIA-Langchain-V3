from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrCloseReasons() -> list:
    """Retrieves master justification reasons for project closure from GET /api/pr-close-reasons.
    Database and JSON fields returned per record:
    - reason_id / id (int) [PRIMARY KEY / FOREIGN KEY]: Closure reason code ID.
    - reason_desc / description (str): Official closure justification (e.g. 'Successfully Completed', 'Client Terminated', 'Budget Exhausted').
    Maps to GET /api/pr-close-reasons."""
    return make_request("/api/pr-close-reasons")

@tool
def fetchPrCloseReasonsByPrType(prType: str) -> list:
    """Retrieves closure reasons filtered by project type classification (prType).
    Maps to GET /api/pr-close-reasons/pr-type/{prType}."""
    if not prType or not str(prType).strip():
        return {"error": "Project type cannot be empty"}
    return make_request(f"/api/pr-close-reasons/pr-type/{str(prType).strip()}")

@tool
def fetchPrCloseReasonsByReason(clReason: str) -> list:
    """Retrieves closure reasons filtered by reason description keyword (clReason).
    Maps to GET /api/pr-close-reasons/reason/{clReason}."""
    if not clReason or not str(clReason).strip():
        return {"error": "Reason cannot be empty"}
    return make_request(f"/api/pr-close-reasons/reason/{str(clReason).strip()}")
