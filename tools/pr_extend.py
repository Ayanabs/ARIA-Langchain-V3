from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrExtends() -> list:
    """Retrieves all PR extension records. Maps to /api/pr-extends."""
    return make_request("/api/pr-extends")

@tool
def fetchPrExtendsByExId(exId: str) -> list:
    """Retrieves PR extension records filtered by extension ID (ex_id). Maps to /api/pr-extends/ex-id/{exId}."""
    cleaned = clean_id(exId)
    if not cleaned:
        return {"error": f"Invalid extension ID format: {exId}"}
    return make_request(f"/api/pr-extends/ex-id/{cleaned}")

@tool
def fetchPrExtendsByExtendedDate(extendedDate: str) -> list:
    """Retrieves PR extension records filtered by extended date (YYYY-MM-DD). Maps to /api/pr-extends/extended-date/{extendedDate}."""
    if not extendedDate or not str(extendedDate).strip():
        return {"error": "Extended date cannot be empty"}
    return make_request(f"/api/pr-extends/extended-date/{quote(extendedDate)}")

@tool
def fetchPrExtendsByEdate(edate: str) -> list:
    """Retrieves PR extension records filtered by edate (YYYY-MM-DD). Maps to /api/pr-extends/edate/{edate}."""
    if not edate or not str(edate).strip():
        return {"error": "End date (edate) cannot be empty"}
    return make_request(f"/api/pr-extends/edate/{quote(edate)}")
