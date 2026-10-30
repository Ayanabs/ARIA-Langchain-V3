from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrChangeHistories() -> list:
    """Retrieves audit revision and extension logs for PR projects from GET /api/pr-change-histories.
    Database and JSON fields returned per record:
    - id (int): Primary key audit log ID.
    - pr_code / code (str) [FOREIGN KEY]: PR project code (linking to 'code' in 'pr_projects').
    - change_type (str): Type of project modification ('Extension', 'Budget Revision', 'Scope Change').
    - change_date (str): Date change was logged (Format: YYYY-MM-DD).
    - prev_end_date (str): Original target end date prior to extension.
    - new_end_date (str): Updated target completion date after extension.
    - user_id (str): User ID of administrator who logged the change.
    Maps to GET /api/pr-change-histories."""
    return make_request("/api/pr-change-histories")

@tool
def fetchPrChangeHistoryBySerialNo(serialNo: int) -> list:
    """Retrieves change history records for a project by primary key serial sequence number (serialNo [PK]).
    Maps to GET /api/pr-change-history/serial-no/{serialNo}."""
    return make_request(f"/api/pr-change-history/serial-no/{serialNo}")

@tool
def fetchPrChangeHistoriesByProjectCode(prCode: str) -> list:
    """Retrieves revision and extension history for a specific PR project code (prCode).
    Arguments & Foreign Key:
    - prCode (str) [FOREIGN KEY]: Project code linking to 'code' in 'pr_projects'.
    Maps to GET /api/pr-change-histories/project-code/{prCode}."""
    if not prCode or not str(prCode).strip():
        return {"error": "Project code cannot be empty"}
    return make_request(f"/api/pr-change-history/project-code/{quote(prCode)}")

@tool
def fetchPrChangeHistoryByNewApCode(newApCode: str) -> list:
    """Retrieves change history records filtered by updated AP code (newApCode).
    Maps to GET /api/pr-change-history/new-ap-code/{newApCode}."""
    if not newApCode or not str(newApCode).strip():
        return {"error": "AP code cannot be empty"}
    return make_request(f"/api/pr-change-history/new-ap-code/{quote(newApCode)}")

@tool
def fetchPrChangeHistoryByApCodeYear(apCodeYear: str) -> list:
    """Retrieves change history records filtered by AP code year (apCodeYear).
    Maps to GET /api/pr-change-history/ap-code-year/{apCodeYear}."""
    if not apCodeYear or not str(apCodeYear).strip():
        return {"error": "AP code year cannot be empty"}
    return make_request(f"/api/pr-change-history/ap-code-year/{quote(apCodeYear)}")
