from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllSaLocations() -> list:
    """Retrieves Space Applications Division satellite ground station and field site locations from GET /api/sa-locations.
    Database and JSON fields returned per record:
    - location_id / id (int) [PRIMARY KEY / FOREIGN KEY]: Ground station location code.
    - location_name (str): Location name (e.g. 'Arthur C Clarke Institute Observatory', 'Kandy Ground Station').
    - district (str): District/region name.
    Maps to GET /api/sa-locations."""
    return make_request("/api/sa-locations")
