from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllClaimTypes() -> list:
    """Retrieves all official claim types from GET /api/claim-types.
    Database & JSON fields returned per record:
    - C_Type_Id (int) [PRIMARY KEY / FOREIGN KEY]: Claim type unique identifier code.
    - C_Type / cType (str): Claim type description (e.g. 'Overtime Claim', 'Travel Allowance', 'Medical Reimbursement').
    Maps to GET /api/claim-types."""
    return make_request("/api/claim-types")

@tool
def fetchClaimTypeByType(cType: str) -> dict:
    """Retrieves claim type details by description or name (cType).
    Returns fields: C_Type_Id [PK/FK], C_Type (description).
    Maps to GET /api/claim-types/type/{cType}."""
    if not cType or not str(cType).strip():
        return {"error": "Claim type cannot be empty"}

    return make_request(f"/api/claim-types/type/{cType}")
