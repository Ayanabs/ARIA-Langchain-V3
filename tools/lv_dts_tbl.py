from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllLeaveDates() -> list:
    """Retrieves leave date breakdown records for approved leave applications from GET /api/leave-dates.
    Database and JSON fields returned per record:
    - id (int): Primary key leave date breakdown ID.
    - Leave_ID (int) [FOREIGN KEY]: Foreign key linking to primary leave application ID in 'emp_lv_tbl'.
    - Leave_Date (str): Calendar date of leave (Format: YYYY-MM-DD).
    - No_of_Days (float): Duration weight for the day (1.0 = Full Day, 0.5 = Half Day).
    Maps to GET /api/leave-dates."""
    return make_request("/api/leave-dates")

@tool
def fetchLeaveDatesByLeaveId(leaveId: int) -> list:
    """Retrieves leave date breakdown days for a specific leave application using Leave_ID.
    Arguments & Foreign Key:
    - leaveId (int) [FOREIGN KEY]: Foreign key linking to 'id' in 'emp_lv_tbl'.
    Returns fields: id, Leave_ID [FK], Leave_Date, No_of_Days (1.0 = full day, 0.5 = half day).
    Maps to GET /api/leave-dates/leave-id/{leaveId}."""
    cleaned = clean_id(leaveId)
    if not cleaned:
        return {"error": f"Invalid leave ID format: {leaveId}"}
    return make_request(f"/api/leave-dates/leave-id/{cleaned}")

@tool
def fetchLeaveDatesByLeaveDate(leaveDate: str) -> list:
    """Retrieves leave date records filtered by calendar date (leaveDate, Format: YYYY-MM-DD).
    Maps to GET /api/leave-dates/date/{leaveDate}."""
    if not leaveDate or not str(leaveDate).strip():
        return {"error": "Leave date cannot be empty"}
    return make_request(f"/api/leave-dates/date/{str(leaveDate).strip()}")
