from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpSecurities() -> list:
    """Retrieves security staff roster and gate post duty assignments from GET /api/emp-securities.
    Database and JSON fields returned per record:
    - id (int): Primary key duty record ID.
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - Shift (str): Assigned guard shift ('Day', 'Night').
    - Post (str): Assigned entrance gate or security post location.
    Maps to GET /api/emp-securities."""
    return make_request("/api/emp-securities")

@tool
def fetchEmpSecuritiesByShift(shift: str) -> list:
    """Retrieves security staff duty assignments filtered by shift ('Day' or 'Night').
    Returns fields: id, EmpNo [FK], Shift, Post.
    Maps to GET /api/emp-securities/shift/{shift}."""
    if not shift or not str(shift).strip():
        return {"error": "Shift cannot be empty"}

    return make_request(f"/api/emp-securities/shift/{str(shift).strip()}")

@tool
def fetchEmpSecuritiesByPost(post: str) -> list:
    """Retrieves security staff duty assignments filtered by security post or entrance gate location.
    Returns fields: id, EmpNo [FK], Shift, Post.
    Maps to GET /api/emp-securities/post/{post}."""
    if not post or not str(post).strip():
        return {"error": "Post cannot be empty"}

    return make_request(f"/api/emp-securities/post/{str(post).strip()}")

@tool
def fetchEmpSecuritiesByRank(rank: str) -> list:
    """Retrieves security staff records filtered by rank designation. Maps to GET /api/emp-securities/rank/{rank}."""
    cleaned = clean_id(rank) if isinstance(rank, (int, str)) else str(rank)
    if not cleaned:
        return {"error": f"Invalid rank format: {rank}"}
    return make_request(f"/api/emp-securities/rank/{rank}".format(rank=cleaned))

@tool
def fetchEmpSecuritiesByStatus(status: str) -> list:
    """Retrieves security staff records filtered by duty status. Maps to GET /api/emp-securities/status/{status}."""
    cleaned = clean_id(status) if isinstance(status, (int, str)) else str(status)
    if not cleaned:
        return {"error": f"Invalid status format: {status}"}
    return make_request(f"/api/emp-securities/status/{status}".format(status=cleaned))
