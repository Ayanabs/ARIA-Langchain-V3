from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrDenyClosedprjs() -> list:
    """Retrieves rejected project closure request logs from GET /api/pr-deny-closedprj.
    Database and JSON fields returned per record:
    - id (int): Primary key rejection record ID.
    - pr_code / code (str) [FOREIGN KEY]: Project code (linking to 'code' in 'pr_projects').
    - rejection_reason (str): Reason project closure request was denied by management.
    - deny_date (str): Date closure rejection was issued (Format: YYYY-MM-DD).
    Maps to GET /api/pr-deny-closedprj."""
    return make_request("/api/pr-deny-closedprj")


@tool
def fetchPrDenyClosedprjByPCode(pCode: str) -> dict:
    """Retrieves rejected project closure request log for a specific project by Project Code (pCode [FK]).
    Maps to GET /api/pr-deny-closed-projects/{pCode}."""
    cleaned = clean_id(pCode)
    if not cleaned:
        return {"error": "Invalid project code format"}
    return make_request(f"/api/pr-deny-closed-projects/{cleaned}")


@tool
def fetchPrDenyClosedprjByCloseReason(closeReason: str) -> list:
    """Retrieves denied project closures filtered by close reason keyword.
    Maps to GET /api/pr-deny-closed-projects/close-reason/{closeReason}."""
    if not closeReason or not str(closeReason).strip():
        return {"error": "Close reason cannot be empty"}
    return make_request(f"/api/pr-deny-closed-projects/close-reason/{str(closeReason).strip()}")

