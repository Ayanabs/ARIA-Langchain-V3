from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrEduLevelsDes() -> list:
    """Retrieves education level detailed descriptions from GET /api/hr-edu-levels-des.
    Database and JSON fields returned per record:
    - id (int): Primary key record ID.
    - EduLevelID (int) [FOREIGN KEY]: Foreign key linking to 'EduLevelID' in 'hr_edu_levels'.
    - Description (str): Detailed qualification description or minimum eligibility requirements.
    Maps to GET /api/hr-edu-levels-des."""
    return make_request("/api/hr-edu-levels-des")
