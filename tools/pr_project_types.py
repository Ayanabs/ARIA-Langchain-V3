from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrProjectTypes() -> list:
    """Retrieves all PR project types. Maps to /api/pr-project-types."""
    return make_request("/api/pr-project-types")

@tool
def fetchPrProjectTypeByCode(ptCode: int) -> dict:
    """Retrieves PR project type definition by primary key project type code (ptCode [PK]).
    Maps to GET /api/pr-project-types/{ptCode}."""
    return make_request(f"/api/pr-project-types/{ptCode}")


@tool
def fetchPrProjectTypesByShortDescription(ptShortDes: str) -> list:
    """Retrieves PR project types filtered by short description. Maps to /api/pr-project-types/short-description/{ptShortDes}."""
    if not ptShortDes or not str(ptShortDes).strip():
        return {"error": "Short description cannot be empty"}
    return make_request(f"/api/pr-project-types/short-description/{quote(ptShortDes)}")


@tool
def fetchPrProjectTypesByDescription(ptDescription: str) -> list:
    """Retrieves PR project types filtered by full description. Maps to /api/pr-project-types/description/{ptDescription}."""
    if not ptDescription or not str(ptDescription).strip():
        return {"error": "Description cannot be empty"}
    return make_request(f"/api/pr-project-types/description/{quote(ptDescription)}")

@tool
def fetchPrProjectTypesBySkillCode(ptSkcode: str) -> list:
    """Retrieves PR project types filtered by skill code. Maps to /api/pr-project-types/skill-code/{ptSkcode}."""
    if not ptSkcode or not str(ptSkcode).strip():
        return {"error": "Skill code cannot be empty"}
    return make_request(f"/api/pr-project-types/skill-code/{quote(ptSkcode)}")