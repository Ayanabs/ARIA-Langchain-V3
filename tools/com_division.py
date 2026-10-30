from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllComDivisions() -> list:
    """Retrieves internal sub-division hierarchy linkage records (divId, mdivCode, tdivCode) from GET /api/com-divisions.
    NOTE: This is NOT the Communication Division (COM) or general division catalog.
    For the Communication Division or general institute divisions, use fetchDivisionByShortCode, fetchDivisionByName, or fetchAllDivisions instead.
    JSON fields returned per record:
    - divId (int): Internal row mapping ID.
    - mdivCode (str): Main division code.
    - tdivCode (str): Sub-division / team division code.
    Maps to GET /api/com-divisions."""
    return make_request("/api/com-divisions")

@tool
def fetchComDivisionByMdivCode(mdivCode: str) -> dict:
    """Retrieves internal sub-division hierarchy linkage record by main division code (mdivCode) from GET /api/com-divisions.
    NOTE: This is NOT the Communication Division (COM). For general institute division details, use fetchDivisionByCode or fetchDivisionByShortCode instead.
    JSON fields returned: divId, mdivCode, tdivCode.
    Maps to GET /api/com-divisions/mdiv-code/{mdivCode}."""
    val = str(mdivCode).strip() if mdivCode is not None else ""
    if not val:
        return {"error": "Mdiv code cannot be empty"}

    return make_request(f"/api/com-divisions/mdiv-code/{val}")

@tool
def fetchComDivisionByTdivCode(tdivCode: str) -> dict:
    """Retrieves internal sub-division hierarchy linkage record by team/sub-division code (tdivCode) from GET /api/com-divisions.
    NOTE: This is NOT the Communication Division (COM). For general institute division details, use fetchDivisionByCode or fetchDivisionByShortCode instead.
    JSON fields returned: divId, mdivCode, tdivCode.
    Maps to GET /api/com-divisions/tdiv-code/{tdivCode}."""
    val = str(tdivCode).strip() if tdivCode is not None else ""
    if not val:
        return {"error": "Tdiv code cannot be empty"}

    return make_request(f"/api/com-divisions/tdiv-code/{val}")
