from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrStoresTbl() -> list:
    """Retrieves all PR stores records. Maps to /api/pr-stores."""
    return make_request("/api/pr-stores")

@tool
def fetchPrStoresTblByStCode(stCode: str) -> list:
    """Retrieves PR stores records filtered by store code. Maps to /api/pr-stores/st-code/{stCode}."""
    if not stCode or not str(stCode).strip():
        return {"error": "Store code cannot be empty"}
    return make_request(f"/api/pr-stores/st-code/{quote(stCode)}")

@tool
def fetchPrStoresTblBySerialNo(serialNo: str) -> list:
    """Retrieves PR stores records filtered by serial number. Maps to /api/pr-stores/serial-no/{serialNo}."""
    cleaned = clean_id(serialNo)
    if not cleaned:
        return {"error": f"Invalid serial number format: {serialNo}"}
    return make_request(f"/api/pr-stores/serial-no/{cleaned}")
