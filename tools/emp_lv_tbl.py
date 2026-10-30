from typing import Any
from aria_agent.schemas.retrieval import ReadLimit
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpLeaves() -> list:
    """Retrieves all employee leave records across the entire organisation.
    Each record contains: empNo, leaveTypeId, startDate, endDate, leaveDays count,
    reason, and approval status. Use for organisation-wide leave auditing.
    Maps to /api/emp-leaves."""
    return make_request("/api/emp-leaves")

@tool
def fetchEmpLeavesByEmployee(empNo: str) -> list:
    """Retrieves leave records and leave history for a specific employee by employee number (empNo).
    Returns a list of leave entries with fields: empNo, leaveTypeId, startDate, endDate,
    leaveDays count, leave reason, and approval status.
    Use when asked about an employee's leave balance, leave days, taken leaves,
    casual leave, annual leave, medical leave, or vacation history.
    Maps to /api/emp-leaves/employee/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    return make_request(f"/api/emp-leaves/employee/{cleaned}")

@tool
def fetchEmpLeavesByType(leaveTypeId: str) -> list:
    """Retrieves leave records filtered by a specific leave type ID (e.g. casual leave,
    annual leave, medical leave, duty leave).
    Maps to /api/emp-leaves/type/{leaveTypeId}."""
    cleaned = clean_id(leaveTypeId)

    if not cleaned:
        return {"error": f"Invalid leave type ID format: {leaveTypeId}"}

    return make_request(f"/api/emp-leaves/type/{cleaned}")

@tool
def fetchOverseasEmpLeaves() -> list:
    """Retrieves all overseas private and official foreign leave records for employees.
    Contains details of international travel approvals and duration.
    Maps to /api/emp-leaves/overseas."""
    return make_request("/api/emp-leaves/overseas")

@tool
def fetchEmpLeavesByEmpNo(empNo: str) -> Any:
    """Retrieves leave records for a specific employee by empNo. Maps to /api/emp-leaves/employee/{empNo}."""
    return fetchEmpLeavesByEmployee.func(empNo)


@tool
def fetchEmpLeavesByDateRange(
    startDate: str,
    endDate: str,
    fullname: str = "",
    empNo: str = "",
    limit: ReadLimit = 250
) -> list:
    """Retrieves approved employee leave records (annual, casual, medical, duty, vacation) across a calendar date range between startDate and endDate.

    DYNAMIC DATE RANGE GENERATION (startDate and endDate variables):
    - When the user asks for leaves across a time window (e.g. "leaves of Rasika in the last 30 days", "leaves taken within 7 days", "past month leaves", "leaves between X and Y"):
      * You (the LLM) must dynamically compute and set BOTH date variables ('startDate' and 'endDate') in YYYY-MM-DD format based on the prompt:
        1. Relative Days: For "leaves in the last 30 days", calculate startDate = endDate - 30 days.
        2. Known Anchor: If an earlier conversation turn established a historical anchor date, calculate relative to that date.
        3. Calendar Window: For "between 2021-01-01 and 2021-12-31", set startDate='2021-01-01', endDate='2021-12-31'.

    ARGUMENTS:
    - startDate (str): Beginning of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - endDate (str): End of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - fullname (str, optional): Employee full or partial name (e.g. 'Rasika', 'Rasika Nishanthi Somathilake'). Automatically resolves to their employee ID.
    - empNo (str/int, optional): Employee Number (staff ID, e.g. '107').
    - limit (int, optional): Max records to return (default 250).

    RETURNS:
    List of leave records with fields: empNo, date, attendanceType, inTime, outTime.
    Maps to /api/attendance/employee/{empNo} and /api/emp-leaves/employee/{empNo}.
    """
    s_dt = str(startDate).strip() if startDate else ""
    e_dt = str(endDate).strip() if endDate else ""
    if not s_dt or not e_dt:
        return [{"error": "Both startDate and endDate (YYYY-MM-DD) are required"}]

    target_empno = clean_id(empNo) if empNo else ""

    if not target_empno and fullname and str(fullname).strip():
        clean_name = str(fullname).strip()
        try:
            emp_res = make_request(f"/api/employees/fullname/{clean_name}")
            records = emp_res if isinstance(emp_res, list) else ([emp_res] if isinstance(emp_res, dict) else [])
            if len(records) == 1 and isinstance(records[0], dict):
                e_no = records[0].get("empno") or records[0].get("empNo") or records[0].get("id")
                if e_no:
                    target_empno = clean_id(str(e_no))
            elif len(records) > 1:
                matches = []
                for rec in records:
                    if isinstance(rec, dict):
                        from aria_agent.utils.data import extract_empno_from_dict, extract_record_id, extract_record_name
                        matches.append({
                            "empNo": extract_empno_from_dict(rec) or extract_record_id(rec),
                            "fullname": extract_record_name(rec) or clean_name,
                            "designation": rec.get("designation") or "N/A",
                            "division": rec.get("division") or "N/A"
                        })
                return [{
                    "status": "ambiguous",
                    "message": f"Found {len(records)} employees matching '{clean_name}'. Please specify by employee number (empNo):",
                    "matching_employees": matches
                }]
        except Exception:
            pass

    if target_empno:
        # Check attendance where attendanceType contains 'Leave'
        att_recs = make_request(f"/api/attendance/employee/{target_empno}")
        leave_days = []
        if isinstance(att_recs, list) and att_recs:
            for a in att_recs:
                if not isinstance(a, dict):
                    continue
                d = str(a.get("date") or "")
                att_type = str(a.get("attendanceType") or "")
                if s_dt <= d <= e_dt and ("Leave" in att_type or "leave" in att_type.lower()):
                    leave_days.append({
                        "empNo": target_empno,
                        "date": d,
                        "attendanceType": att_type,
                        "inTime": a.get("inTime"),
                        "outTime": a.get("outTime")
                    })
            if leave_days:
                sorted_leaves = sorted(leave_days, key=lambda x: str(x.get("date", "")), reverse=True)
                return sorted_leaves[:limit] if limit else sorted_leaves

        leaves = make_request(f"/api/emp-leaves/employee/{target_empno}")
        if isinstance(leaves, list) and leaves:
            return leaves[:limit] if limit else leaves

    return [{"notice": f"No leave records found between {s_dt} and {e_dt}."}]

