from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllMainSubDivisions() -> list:
    """Retrieves parent-child sub-division hierarchy mappings from GET /api/main-sub-divisions.
    Database and JSON fields returned per record:
    - div_id / id (int): Primary key hierarchy mapping ID.
    - main_div_code (int) [FOREIGN KEY]: Parent numeric division code (linking to 'divisioncode' in 'division').
    - child_div_code (int) [FOREIGN KEY]: Sub-division/child numeric division code (linking to 'divisioncode' in 'division').
    Maps to GET /api/main-sub-divisions."""
    return make_request("/api/main-sub-divisions")

@tool
def fetchMainSubDivisionsByMainDivCode(mainDivCode: str) -> list:
    """Retrieves sub-divisions belonging to a specific parent division using mainDivCode.
    Arguments & Foreign Key:
    - mainDivCode (str) [FOREIGN KEY]: Parent division code returned by the authorized lookup.
    Maps to GET /api/main-sub-divisions/main-div/{mainDivCode}."""
    cleaned = mainDivCode.strip()
    if not cleaned:
        return {"error": "Invalid mainDivCode"}
    return make_request(f"/api/main-sub-divisions/main-div/{quote(cleaned, safe='')}")

@tool
def fetchMainSubDivisionsByChildDivCode(childDivCode: int) -> list:
    """Retrieves parent division mapping for a specific sub-division using childDivCode.
    Arguments & Foreign Key:
    - childDivCode (int) [FOREIGN KEY]: Child numeric division code linking to 'divisioncode' in 'division'.
    Maps to GET /api/main-sub-divisions/child-div/{childDivCode}."""
    cleaned = clean_id(childDivCode)
    if not cleaned:
        return {"error": "Invalid childDivCode"}
    return make_request(f"/api/main-sub-divisions/child-div/{cleaned}")
