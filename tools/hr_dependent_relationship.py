from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrDependentRelationships() -> list:
    """Retrieves the complete master lookup table of family relationship definitions from GET /api/hr-dependent-relationships.
    Database and JSON fields returned per record:
    - iD (int) [PRIMARY KEY]: Numeric relationship code identifier (1=Husband, 2=Wife, 3=Son, 4=Daughter, 5=Father, 6=Mother, 7=Other).
    - relationship (str): Human-readable family relationship title string (e.g. 'Husband', 'Wife', 'Son', 'Daughter', 'Father', 'Mother', 'Other').
    SCHEMA RELATION & FOREIGN KEY MAPPING:
    This master lookup table contains the PRIMARY KEY ('iD') referenced by the FOREIGN KEY ('relationship') in the employee dependent details table 'hr_depdetails' (tools: 'fetchHrDepDetailsByEmployee', 'fetchAllHrDepDetails').
    When answering queries about an employee's family, relations, relatives, spouse, children, or dependents, call this tool alongside 'fetchHrDepDetailsByEmployee' so that numeric relationship foreign keys (e.g. 1, 2, 3, 4) can be accurately resolved to their titles ('Husband', 'Wife', 'Son', 'Daughter', etc.).
    Maps to GET /api/hr-dependent-relationships."""
    return make_request("/api/hr-dependent-relationships")

@tool
def searchHrDependentRelationshipsByName(name: str) -> list:
    """Searches family relationship definitions by title name (e.g. 'Spouse', 'Husband', 'Wife', 'Son', 'Daughter', 'Father', 'Mother').
    Returns fields:
    - iD (int) [PRIMARY KEY]: Numeric relationship code identifier (which is used as the 'relationship' FK in 'hr_depdetails').
    - relationship (str): Family relationship title string.
    Use this tool when you need the numeric relationship ID code corresponding to a specific relationship title before querying 'fetchHrDepDetailsByRelationship'.
    Maps to GET /api/hr-dependent-relationships/search?name={name}."""
    if not name or not str(name).strip():
        return {"error": "Name cannot be empty"}
    return make_request(f"/api/hr-dependent-relationships/search?name={quote(name)}")
