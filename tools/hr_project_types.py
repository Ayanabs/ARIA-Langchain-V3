from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrProjectTypes() -> list:
    """Retrieves HR project type classification categories from GET /api/hr-project-types.
    Database and JSON fields returned per record:
    - pt_code (int) [PRIMARY KEY / FOREIGN KEY]: Numeric project type code. Referenced by 'pt_code' in 'hr_projects'.
    - pt_short_des (str): Short acronym or brief project type description.
    - pt_description (str): Full project classification description (e.g. 'Research and Development', 'Consultancy', 'Testing and Calibration').
    Maps to GET /api/hr-project-types."""
    return make_request("/api/hr-project-types")

@tool
def fetchHrProjectTypesByShortDescription(ptShortDes: str) -> list:
    """Retrieves project types filtered by short acronym description (ptShortDes).
    Maps to GET /api/hr-project-types/short-description/{ptShortDes}."""
    if not ptShortDes or not str(ptShortDes).strip():
        return {"error": "Short description cannot be empty"}
    return make_request(f"/api/hr-project-types/short-description/{quote(ptShortDes)}")

@tool
def fetchHrProjectTypesByDescription(ptDescription: str) -> list:
    """Retrieves project types filtered by full description string (ptDescription).
    Maps to GET /api/hr-project-types/description/{ptDescription}."""
    if not ptDescription or not str(ptDescription).strip():
        return {"error": "Description cannot be empty"}
    return make_request(f"/api/hr-project-types/description/{quote(ptDescription)}")
