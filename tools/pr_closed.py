from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrCloseds() -> list:
    """Retrieves completed and closed PR project records from GET /api/pr-closed.
    Database and JSON fields returned per record:
    - id (int): Primary key closed project record ID.
    - pr_code / code (str) [FOREIGN KEY]: Project code (linking to 'code' in 'pr_projects').
    - close_date (str): Date project was officially closed (Format: YYYY-MM-DD).
    - close_reason_id (int) [FOREIGN KEY]: Reason ID linking to 'reason_id' in 'pr_close_reasons'.
    - final_cost (float): Final actual expenditure total.
    Maps to GET /api/pr-closed."""
    return make_request("/api/pr-closed")

@tool
def fetchPrClosedByClId(clId: int) -> list:
    """Retrieves closed project records by closure sequence ID (clId).
    Maps to GET /api/pr-closed/cl-id/{clId}."""
    return make_request(f"/api/pr-closed/cl-id/{clId}")

@tool
def fetchPrClosedByPType(pType: str) -> list:
    """Retrieves closed project records filtered by project type classification (pType).
    Maps to GET /api/pr-closed/p-type/{pType}."""
    if not pType or not str(pType).strip():
        return {"error": "Project type cannot be empty"}
    return make_request(f"/api/pr-closed/p-type/{str(pType).strip()}")

@tool
def fetchPrClosedByClReason(clReason: str) -> list:
    """Retrieves closed project records filtered by closure reason keyword.
    Maps to GET /api/pr-closed/cl-reason/{clReason}."""
    if not clReason or not str(clReason).strip():
        return {"error": "Close reason cannot be empty"}
    return make_request(f"/api/pr-closed/cl-reason/{str(clReason).strip()}")
