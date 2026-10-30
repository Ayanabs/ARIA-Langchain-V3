from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQALSubjects() -> list:
    """Retrieves G.C.E. Advanced Level (A/L) subject master directory from GET /api/hr-q-al-subjects.
    Database and JSON fields returned per record:
    - Sub_No / subNo (str/int) [PRIMARY KEY / FOREIGN KEY]: Unique A/L subject numeric code. Referenced by 'ALSubNo' in 'hr_q_al'.
    - Sub_Name / subName (str): Official G.C.E. A/L subject name (e.g. 'Combined Mathematics', 'Physics', 'Chemistry', 'Biology', 'Economics').
    Maps to GET /api/hr-q-al-subjects."""
    return make_request("/api/hr-q-al-subjects")

@tool
def fetchHrQALSubjectsBySubjectName(subName: str) -> list:
    """Retrieves G.C.E. A/L subject details by subject name (e.g. 'Combined Mathematics', 'Physics').
    Returns fields: Sub_No [PK/FK], Sub_Name.
    Maps to GET /api/hr-q-al-subjects/name/{subName}."""
    if not subName or not str(subName).strip():
        return {"error": "Subject name cannot be empty"}
    return make_request(f"/api/hr-q-al-subjects/name/{quote(subName)}")
