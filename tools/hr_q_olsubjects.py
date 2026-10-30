from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQOLSubjects() -> list:
    """Retrieves G.C.E. Ordinary Level (O/L) subject master directory from GET /api/hr-q-ol-subjects.
    Database and JSON fields returned per record:
    - Sub_No / subNo (str/int) [PRIMARY KEY / FOREIGN KEY]: Unique O/L subject numeric code. Referenced by 'olSubNo' in 'hr_q_ol'.
    - Sub_Name / subName (str): Official G.C.E. O/L subject name (e.g. 'Mathematics', 'Science', 'English', 'Sinhala', 'History').
    Maps to GET /api/hr-q-ol-subjects."""
    return make_request("/api/hr-q-ol-subjects")
