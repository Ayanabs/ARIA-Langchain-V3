from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQHiEdus() -> list:
    """Retrieves higher education qualification master list from GET /api/hr-q-hi-edu.
    Database and JSON fields returned per record:
    - HiEdu_No / id (int) [PRIMARY KEY / FOREIGN KEY]: Higher education qualification code identifier.
    - HiEdu_Name / title (str): Qualification title (e.g. 'Bachelor of Science', 'Master of Science', 'Doctor of Philosophy', 'Diploma in Management').
    Maps to GET /api/hr-q-hi-edu."""
    return make_request("/api/hr-q-hi-edu")

@tool
def fetchHrQHieduByEmpNo(empNo: str) -> list:
    """Retrieves higher education qualifications for a specific employee by Employee Number (empNo [FK]).
    Maps to GET /api/hr-q-hi-edu/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/hr-q-hi-edu/employee/{cleaned}")
