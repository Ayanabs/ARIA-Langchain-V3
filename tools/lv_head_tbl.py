from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllLeaveHeads() -> list:
    """Retrieves Head of Division (HOD) leave recommendation and approval records from GET /api/leave-heads.
    Database and JSON fields returned per record:
    - id (int): Primary key recommendation ID.
    - Leave_ID (int) [FOREIGN KEY]: Foreign key linking to leave application in 'emp_lv_tbl'.
    - Head_EmpNo (str/int) [FOREIGN KEY]: Employee Number of Head of Division recommending the leave (linking to 'empno' in 'employee').
    - Status (str): HOD recommendation status ('Recommended', 'Not Recommended', 'Pending').
    - Remarks (str): HOD recommendation comments or remarks.
    Maps to GET /api/leave-heads."""
    return make_request("/api/leave-heads")

@tool
def fetchLeaveHeadsByLeaveId(leaveId: int) -> list:
    """Retrieves HOD recommendation records for a specific leave application using Leave_ID.
    Arguments & Foreign Key:
    - leaveId (int) [FOREIGN KEY]: Foreign key linking to 'id' in 'emp_lv_tbl'.
    Returns fields: id, Leave_ID [FK], Head_EmpNo [FK], Status, Remarks.
    Maps to GET /api/leave-heads/leave-id/{leaveId}."""
    cleaned = clean_id(leaveId)
    if not cleaned:
        return {"error": f"Invalid leave ID format: {leaveId}"}
    return make_request(f"/api/leave-heads/leave-id/{cleaned}")

@tool
def fetchLeaveHeadsByEmpNo(empNo: str) -> list:
    """Retrieves HOD leave recommendations for an employee by Employee Number (empNo [FK]).
    Maps to GET /api/leave-heads/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/leave-heads/employee/{cleaned}")

@tool
def fetchLeaveHeadsByHodEmpNo(hodEmpNo: str) -> list:
    """Retrieves leave applications reviewed or recommended by a specific Head of Division using Head_EmpNo (hodEmpNo [FK]).
    Maps to GET /api/leave-heads/head/{hodEmpNo}."""
    cleaned = clean_id(hodEmpNo)
    if not cleaned:
        return {"error": f"Invalid head employee number format: {hodEmpNo}"}
    return make_request(f"/api/leave-heads/head/{cleaned}")

@tool
def fetchLeaveHeadsByHeadEmpNo(headEmpNo: str) -> list:
    """Retrieves leave applications reviewed or recommended by a specific Head of Division using Head_EmpNo.
    Maps to GET /api/leave-heads/head-emp-no/{headEmpNo}."""
    cleaned = clean_id(headEmpNo)
    if not cleaned:
        return {"error": f"Invalid head employee number format: {headEmpNo}"}
    return make_request(f"/api/leave-heads/head-emp-no/{cleaned}")
