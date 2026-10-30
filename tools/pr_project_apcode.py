from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrProjectApcodes() -> list:
    """Retrieves all PR project AP codes. Maps to /api/pr-project-ap-codes."""
    return make_request("/api/pr-project-ap-codes")

@tool
def fetchPrProjectApcodesByApcode(apcode: str) -> list:
    """Retrieves PR project AP codes filtered by apcode string. Maps to /api/pr-project-ap-codes/apcode/{apcode}."""
    if not apcode or not str(apcode).strip():
        return {"error": "AP code cannot be empty"}
    return make_request(f"/api/pr-project-ap-codes/apcode/{quote(apcode)}")

@tool
def fetchPrProjectApcodesByYear(year: str) -> list:
    """Retrieves PR project AP codes filtered by year. Maps to /api/pr-project-ap-codes/year/{year}."""
    cleaned = clean_id(year)
    if not cleaned:
        return {"error": f"Invalid year format: {year}"}
    return make_request(f"/api/pr-project-ap-codes/year/{cleaned}")
