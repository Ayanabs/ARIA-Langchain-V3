from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllLeaveHeadPrs() -> list:
    """Retrieves Project Director / Project Manager leave approval records from GET /api/leave-head-prs.
    Database and JSON fields returned per record:
    - id (int): Primary key project approval ID.
    - Leave_ID (int) [FOREIGN KEY]: Foreign key linking to leave application in 'emp_lv_tbl'.
    - PrHead_EmpNo (str/int) [FOREIGN KEY]: Employee Number of Project Leader/Manager (linking to 'empno' in 'employee').
    - Status (str): Project lead approval status ('Approved', 'Pending', 'Rejected').
    - Remarks (str): Project lead remarks or comments.
    Maps to GET /api/leave-head-prs."""
    return make_request("/api/leave-head-prs")

@tool
def fetchLeaveHeadPrsByLeaveId(leaveId: int) -> list:
    """Retrieves project lead approval records for a specific leave application using Leave_ID.
    Arguments & Foreign Key:
    - leaveId (int) [FOREIGN KEY]: Foreign key linking to 'id' in 'emp_lv_tbl'.
    Returns fields: id, Leave_ID [FK], PrHead_EmpNo [FK], Status, Remarks.
    Maps to GET /api/leave-head-prs/leave-id/{leaveId}."""
    cleaned = clean_id(leaveId)
    if not cleaned:
        return {"error": f"Invalid leave ID format: {leaveId}"}
    return make_request(f"/api/leave-head-prs/leave-id/{cleaned}")

@tool
def fetchLeaveHeadPrsByEmpNo(empNo: str) -> list:
    """Retrieves project lead leave approval records for an employee by Employee Number (empNo [FK]).
    Maps to GET /api/leave-heads-pr/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/leave-heads-pr/employee/{cleaned}")

@tool
def fetchLeaveHeadPrsByHodEmpNo(hodEmpNo: str) -> list:
    """Retrieves project lead leave approval records by Project Head Employee Number (hodEmpNo [FK]).
    Maps to GET /api/leave-heads-pr/head/{hodEmpNo}."""
    cleaned = clean_id(hodEmpNo)
    if not cleaned:
        return {"error": f"Invalid project head employee number format: {hodEmpNo}"}
    return make_request(f"/api/leave-heads-pr/head/{cleaned}")

@tool
def fetchLeaveHeadPrsByPrHeadEmpNo(prHeadEmpNo: str) -> list:
    """Retrieves leave applications reviewed by a specific Project Director/Manager using PrHead_EmpNo.
    Maps to GET /api/leave-heads-pr/head/{prHeadEmpNo}."""
    cleaned = clean_id(prHeadEmpNo)
    if not cleaned:
        return {"error": f"Invalid PR head employee number format: {prHeadEmpNo}"}
    return make_request(f"/api/leave-heads-pr/head/{cleaned}")
