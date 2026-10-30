from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllIncompleteSources() -> list:
    """Retrieves incomplete data source flags and error log definitions from GET /api/incomplete-sources.
    Database and JSON fields returned per record:
    - ID (int) [PRIMARY KEY / FOREIGN KEY]: Incomplete source error code ID.
    - Description (str): Error description or missing data source details.
    Maps to GET /api/incomplete-sources."""
    return make_request("/api/incomplete-sources")

@tool
def fetchIncompleteSourcesByDescription(description: str) -> list:
    """Retrieves incomplete source records filtered by error description text.
    Maps to GET /api/incomplete-sources/description/{description}."""
    if not description or not str(description).strip():
        return {"error": "Description cannot be empty"}
    return make_request(f"/api/incomplete-sources/description/{quote(description)}")
