from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllDayTypes() -> list:
    """Retrieves all calendar day type classifications from GET /api/day-types.
    Database and JSON fields returned per record:
    - DayType_ID (int) [PRIMARY KEY / FOREIGN KEY]: Day type code identifier.
    - DayType (str): Description of day classification (e.g. 'Working Day', 'Poya Day', 'Public Holiday', 'Mercantile Holiday', 'Weekend').
    Maps to GET /api/day-types."""
    return make_request("/api/day-types")

@tool
def fetchDayTypeByType(dayType: str) -> dict:
    """Retrieves calendar day type details by description or name (dayType).
    Returns fields: DayType_ID [PK/FK], DayType (description).
    Maps to GET /api/day-types/type/{dayType}."""
    if not dayType or not str(dayType).strip():
        return {"error": "Day type cannot be empty"}

    return make_request(f"/api/day-types/type/{dayType}")
