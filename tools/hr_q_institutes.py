from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQInstitutes() -> list:
    """Retrieves university and educational institute master directory from GET /api/hr-q-institutes.
    Database and JSON fields returned per record:
    - Institute_No / id (int) [PRIMARY KEY / FOREIGN KEY]: Institute numeric identifier code.
    - Institute_Name / name (str): Full official university or educational institute name.
    Maps to GET /api/hr-q-institutes."""
    return make_request("/api/hr-q-institutes")
