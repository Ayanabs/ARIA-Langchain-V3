from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllDesignations() -> list:
    """Retrieves all designation job titles across the organisation from GET /api/designations.
    Database and JSON fields returned per record:
    - DesignationCode / desigcode (int) [PRIMARY KEY / FOREIGN KEY]: Unique designation numeric identifier code. Referenced by 'desigcode' in 'employee', 'hr_official_details', 'positions_tbl'.
    - Designation / designation (str): Official designation job title (e.g. 'Senior Scientific Officer', 'Management Assistant', 'Director').
    Maps to GET /api/designations."""
    return make_request("/api/designations")

@tool
def fetchDesignationByCode(code: int) -> dict:
    """Retrieves designation details by numeric designation code (code).
    Arguments & Foreign Key:
    - code (int) [FOREIGN KEY]: Designation code linking to 'desigcode' in 'employee' and 'hr_official_details'.
    Returns fields: DesignationCode [PK/FK], Designation (title).
    Maps to GET /api/designations/code/{code}."""
    cleaned = clean_id(code)
    if not cleaned:
        return {"error": "Invalid designation code"}
    return make_request(f"/api/designations/code/{cleaned}")

@tool
def fetchDesignationByName(name: str) -> dict:
    """Retrieves designation details by full or partial designation job title.
    Returns fields: DesignationCode [PK/FK], Designation (title).
    Maps to GET /api/designations/name/{name}."""
    if not name or not str(name).strip():
        return {"error": "Designation name cannot be empty"}
    return make_request(f"/api/designations/name/{str(name).strip()}")
