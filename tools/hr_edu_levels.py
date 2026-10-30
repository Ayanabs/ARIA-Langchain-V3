from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrEduLevels() -> list:
    """Retrieves education level master categories from GET /api/hr-edu-levels.
    Database and JSON fields returned per record:
    - EduLevelID / id (int) [PRIMARY KEY / FOREIGN KEY]: Education level numeric code identifier.
    - LevelName / eduLevel (str): Education level title (e.g. 'G.C.E. O/L', 'G.C.E. A/L', 'Diploma', 'Bachelors', 'Masters', 'Doctorate').
    Maps to GET /api/hr-edu-levels."""
    return make_request("/api/hr-edu-levels")
