from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrStores() -> list:
    """Retrieves HR store inventory item allocations from GET /api/hr-stores.
    Database and JSON fields returned per record:
    - st_id (int): Primary key store item record ID.
    - serial_no (int) [FOREIGN KEY]: Row sequence number or item asset tag.
    - st_code / storeCode (str) [FOREIGN KEY]: Store item category code.
    - emp_no / empNo (str/int) [FOREIGN KEY]: Employee Number to whom item is issued (linking to 'empno' in 'employee').
    Maps to GET /api/hr-stores."""
    return make_request("/api/hr-stores")

@tool
def fetchHrStoresByStCode(stCode: str) -> list:
    """Retrieves store inventory items filtered by store item code (stCode).
    Maps to GET /api/hr-stores/st-code/{stCode}."""
    if not stCode or not str(stCode).strip():
        return {"error": "Store code cannot be empty"}
    return make_request(f"/api/hr-stores/st-code/{str(stCode).strip()}")

@tool
def fetchHrStoresBySerialNo(serialNo: str) -> list:
    """Retrieves store inventory items filtered by asset serial number (serialNo).
    Maps to GET /api/hr-stores/serial-no/{serialNo}."""
    cleaned = clean_id(serialNo)
    if not cleaned:
        return {"error": f"Invalid serial number format: {serialNo}"}
    return make_request(f"/api/hr-stores/serial-no/{cleaned}")
