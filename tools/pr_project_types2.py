from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrProjectTypes2() -> list:
    """Retrieves all PR project types 2. Maps to /api/pr-project-types-2."""
    return make_request("/api/pr-project-types-2")

@tool
def fetchPrProjectTypes2ByShortDescription(ptShortDes: str) -> list:
    """Retrieves PR project types 2 filtered by short description. Maps to /api/pr-project-types-2/short-description/{ptShortDes}."""
    if not ptShortDes or not str(ptShortDes).strip():
        return {"error": "Short description cannot be empty"}
    return make_request(f"/api/pr-project-types-2/short-description/{quote(ptShortDes)}")

@tool
def fetchPrProjectTypes2ByDescription(ptDescription: str) -> list:
    """Retrieves PR project types 2 filtered by full description. Maps to /api/pr-project-types-2/description/{ptDescription}."""
    if not ptDescription or not str(ptDescription).strip():
        return {"error": "Description cannot be empty"}
    return make_request(f"/api/pr-project-types-2/description/{quote(ptDescription)}")
