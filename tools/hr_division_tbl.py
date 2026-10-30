from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrDivisions() -> list:
    """Retrieves all HR division records from GET /api/hr-divisions.

    JSON fields returned per record:
    - divisionCode (int): Primary numeric division identifier [FOREIGN KEY].
    - division (str): Full division title.
    - shCode (str): 2-3 letter division acronym (e.g. 'COM', 'DIR', 'ADM', 'ITD', 'ELE').
    - category (str): Category string code (e.g. 'Main').
    Maps to GET /api/hr-divisions."""
    return make_request("/api/hr-divisions")

@tool
def searchHrDivisionsByName(name: str) -> list:
    """Searches HR division records by full or partial division title/name.
    JSON fields returned: divisionCode [FK], division, shCode, category.
    Maps to GET /api/hr-divisions/search?name={name}."""
    if not name or not str(name).strip():
        return {"error": "Division name cannot be empty"}

    return make_request(f"/api/hr-divisions/search?name={quote(name)}")

@tool
def fetchHrDivisionsByCategory(category: str) -> list:
    """Retrieves HR division records matching a category code.
    JSON fields returned: divisionCode [FK], division, shCode, category.
    Maps to GET /api/hr-divisions/category/{category}."""
    if not category or not str(category).strip():
        return {"error": "Category cannot be empty"}

    return make_request(f"/api/hr-divisions/category/{quote(category)}")

@tool
def fetchHrDivisionsByShCode(shCode: str) -> list:
    """Retrieves HR division records matching short code/acronym (shCode).
    JSON fields returned: divisionCode [FK], division, shCode, category.
    Maps to GET /api/hr-divisions/code/{shCode}."""
    if not shCode or not str(shCode).strip():
        return {"error": "Short code cannot be empty"}

    return make_request(f"/api/hr-divisions/code/{quote(shCode)}")
