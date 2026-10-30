from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrPastEnds() -> list:
    """Retrieves all PR past end records. Maps to /api/pr-past-ends."""
    return make_request("/api/pr-past-ends")

@tool
def fetchPrPastEndsByPrCode(prCode: str) -> list:
    """Retrieves PR past end records filtered by PR code. Maps to /api/pr-past-ends/pr-code/{prCode}."""
    if not prCode or not str(prCode).strip():
        return {"error": "PR code cannot be empty"}
    return make_request(f"/api/pr-past-ends/pr-code/{quote(prCode)}")

@tool
def fetchPrPastEndsByEndDate(endDate: str) -> list:
    """Retrieves PR past end records filtered by end date (YYYY-MM-DD). Maps to /api/pr-past-ends/end-date/{endDate}."""
    if not endDate or not str(endDate).strip():
        return {"error": "End date cannot be empty"}
    return make_request(f"/api/pr-past-ends/end-date/{quote(endDate)}")
