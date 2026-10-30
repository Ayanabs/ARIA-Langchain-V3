from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQGrades() -> list:
    """Retrieves examination grade symbols and pass levels from GET /api/hr-q-grades.
    Database and JSON fields returned per record:
    - Grade_No / id (int) [PRIMARY KEY / FOREIGN KEY]: Grade code identifier.
    - Grade_Name / gradeName (str): Exam grade symbol (e.g. 'A' [Distinction], 'B' [Credit], 'C' [Credit], 'S' [Ordinary Pass], 'F' [Fail]).
    Maps to GET /api/hr-q-grades."""
    return make_request("/api/hr-q-grades")

@tool
def searchHrQGradesByName(name: str) -> list:
    """Searches examination grade symbols by grade name or code (e.g. 'A', 'Distinction').
    Returns fields: Grade_No [PK/FK], Grade_Name.
    Maps to GET /api/hr-q-grades/search?name={name}."""
    if not name or not str(name).strip():
        return {"error": "Grade name cannot be empty"}
    return make_request(f"/api/hr-q-grades/search?name={quote(name)}")
