from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpLeaveBkps() -> list:
    """Retrieves historical annual leave balance backup snapshot records from GET /api/emp-lv-tbl-bkp.
    Database and JSON fields returned per record:
    - id (int): Primary key snapshot record ID.
    - emp_no / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - leave_type_id (int) [FOREIGN KEY]: Leave type identifier code (1 = Casual Leave, 2 = Vacation/Casual, 3 = Medical Leave).
    - qty (float): Allocated annual leave entitlement quota.
    - taken_qty (float): Total leave days taken by employee.
    - bal_qty (float): Remaining available leave balance days.
    - valid_dt (str): Entitlement validity expiration date (YYYY-MM-DD).
    Maps to GET /api/emp-lv-tbl-bkp."""
    return make_request("/api/emp-lv-tbl-bkp")

@tool
def fetchEmpLeaveBkpsByEmployee(empNo: str) -> list:
    """Retrieves historical leave balance backup records for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: emp_no [FK], leave_type_id [FK], qty (allocated), taken_qty (taken), bal_qty (balance), valid_dt.
    Maps to GET /api/emp-lv-tbl-bkp/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/emp-lv-tbl-bkp/employee/{cleaned}")

@tool
def fetchEmpLeaveBkpsByType(leaveTypeId: int) -> list:
    """Retrieves historical leave balance backup records filtered by leave type code (leaveTypeId: 1 = Casual, 2 = Vacation, 3 = Medical).
    Maps to GET /api/emp-lv-tbl-bkp/type/{leaveTypeId}."""
    cleaned = clean_id(leaveTypeId)
    if not cleaned:
        return {"error": f"Invalid leave type ID format: {leaveTypeId}"}
    return make_request(f"/api/emp-lv-tbl-bkp/type/{cleaned}")

@tool
def fetchEmpLeaveBkpsByEmpNo(empNo: str) -> list:
    """Retrieves backup leave records for an employee by Employee Number (empNo [FK]). Maps to GET /api/emp-leaves-bkp/employee/{empNo}."""
    cleaned = clean_id(empNo) if isinstance(empNo, (int, str)) else str(empNo)
    if not cleaned:
        return {"error": f"Invalid empNo format: {empNo}"}
    return make_request(f"/api/emp-leaves-bkp/employee/{empNo}".format(empNo=cleaned))
