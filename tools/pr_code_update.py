from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrCodeUpdates() -> list:
    """Retrieves historical project code remapping logs from GET /api/pr-code-updates.
    Database and JSON fields returned per record:
    - id (int): Primary key update log ID.
    - old_code (str): Previous project code.
    - new_code (str) [FOREIGN KEY]: Updated current project code (linking to 'code' in 'pr_projects').
    - update_date (str): Date code remapping was executed (Format: YYYY-MM-DD).
    Maps to GET /api/pr-code-updates."""
    return make_request("/api/pr-code-updates")

@tool
def fetchPrCodeUpdatesByPRCode(pRCode: str) -> list:
    """Retrieves project code update records for a specific project code (pRCode [FK]).
    Maps to GET /api/pr-code-updates/pr-code/{pRCode}."""
    cleaned = clean_id(pRCode)
    if not cleaned:
        return {"error": "Invalid project code format"}
    return make_request(f"/api/pr-code-updates/pr-code/{cleaned}")

@tool
def fetchPrCodeUpdatesByAcPlCode(aCPlCode: str) -> list:
    """Retrieves project code update records filtered by accounting plan code (aCPlCode).
    Maps to GET /api/pr-code-updates/ac-pl-code/{aCPlCode}."""
    if not aCPlCode or not str(aCPlCode).strip():
        return {"error": "AC plan code cannot be empty"}
    return make_request(f"/api/pr-code-updates/ac-pl-code/{str(aCPlCode).strip()}")
