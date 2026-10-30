from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpTypes() -> list:
    """Retrieves all employment type categories from GET /api/employee-types.
    Database and JSON fields returned per record:
    - EmpTypeCode / empTypeCode (str/int) [PRIMARY KEY / FOREIGN KEY]: Employment type code. Referenced by 'emptypecode' in 'employee'.
    - TypeName / typeName (str): Employment type description (e.g. 'Permanent', 'Contract', 'Casual', 'Trainee', 'Temporary').
    Maps to GET /api/employee-types."""
    res = make_request("/api/employee-types")
    if not isinstance(res, list) or (isinstance(res, dict) and "error" in res):
        return make_request("/api/emp-types")
    return res

@tool
def fetchEmpTypeByCode(code: str) -> dict:
    """Retrieves employment type details by code (code).
    Arguments & Foreign Key:
    - code (str/int) [FOREIGN KEY]: Employment type code linking to 'emptypecode' in 'employee'.
    Returns fields: EmpTypeCode [PK/FK], TypeName (description).
    Maps to GET /api/employee-types/{code}."""
    cleaned = clean_id(code)
    if not cleaned:
        return {"error": "Invalid empType code"}
    res = make_request(f"/api/employee-types/{cleaned}")
    if not isinstance(res, dict) or "error" in res:
        return make_request(f"/api/emp-types/code/{cleaned}")
    return res
