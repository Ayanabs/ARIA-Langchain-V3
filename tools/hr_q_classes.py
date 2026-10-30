from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQClasses() -> list:
    """Retrieves academic degree class/grade honor classifications from GET /api/hr-q-classes.
    Database and JSON fields returned per record:
    - Class_No / id (int) [PRIMARY KEY / FOREIGN KEY]: Degree class code identifier.
    - Class_Name / className (str): Class honor title (e.g. 'First Class', 'Second Class Upper', 'Second Class Lower', 'Pass').
    Maps to GET /api/hr-q-classes."""
    return make_request("/api/hr-q-classes")
