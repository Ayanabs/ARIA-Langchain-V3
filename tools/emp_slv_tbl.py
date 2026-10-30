from langchain_core.tools import tool
from aria_agent.schemas.retrieval import ReadLimit
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllEmpShortLeaves() -> list:
    """Retrieves short leave application records for all employees.
    Database and JSON fields returned per record:
    - id / sleaveId (int): Primary key short leave application ID.
    - emp_no / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - slv_dt / leaveDate / attDtId: Short leave date reference.
    - slv_time_from / fromTime (str): Short leave start / leaving time (Format: HH:MM).
    - slv_time_to / toTime (str): Short leave end / return (entry) time (Format: HH:MM).
    - reason / slv_comment (str): Reason or purpose for short leave request.
    - status (str): Application approval status ('Approved', 'Pending', 'Rejected').
    Maps to GET /api/emp-short-leaves."""
    res = make_request("/api/emp-short-leaves")
    if isinstance(res, list) and res:
        return res
    fallback = make_request("/api/emp-slv-tbl")
    return res if isinstance(res, list) else fallback

@tool
def fetchEmpShortLeavesByEmployee(empNo: str) -> list:
    """Retrieves short leave records for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: emp_no [FK], fromTime (leaving time), toTime (return time), reason, status.
    Maps to GET /api/emp-short-leaves/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    res = make_request(f"/api/emp-short-leaves/employee/{cleaned}")
    if isinstance(res, list) and res:
        return res
    fallback = make_request(f"/api/emp-slv-tbl/employee/{cleaned}")
    return res if isinstance(res, list) else fallback

@tool
def fetchEmpShortLeavesByDate(slvDt: str) -> list:
    """Retrieves short leave applications filtered by leave date or attendance date ID (Format: YYYY-MM-DD or numeric ID).
    Maps to GET /api/emp-short-leaves/date/{slvDt}."""
    if not slvDt or not str(slvDt).strip():
        return {"error": "Short leave date cannot be empty"}
    cleaned_date = str(slvDt).strip()
    res = make_request(f"/api/emp-short-leaves/date/{cleaned_date}")
    if isinstance(res, list) and res:
        return res
    fallback = make_request(f"/api/emp-slv-tbl/date/{cleaned_date}")
    return res if isinstance(res, list) else fallback


@tool
def fetchEmpShortLeavesByEmpNo(empNo: str) -> list:
    """Retrieves short leave records for an employee by Employee Number (empNo [FK]). Maps to GET /api/emp-short-leaves/employee/{empNo}."""
    cleaned = clean_id(empNo) if isinstance(empNo, (int, str)) else str(empNo)
    if not cleaned:
        return {"error": f"Invalid empNo format: {empNo}"}
    return make_request(f"/api/emp-short-leaves/employee/{empNo}".format(empNo=cleaned))

@tool
def fetchEmpShortLeavesByAttDtId(attDtId: str) -> list:
    """Retrieves short leave records for an attendance date ID. Maps to GET /api/emp-short-leaves/date/{attDtId}."""
    cleaned = clean_id(attDtId) if isinstance(attDtId, (int, str)) else str(attDtId)
    if not cleaned:
        return {"error": f"Invalid attDtId format: {attDtId}"}
    return make_request(f"/api/emp-short-leaves/date/{attDtId}".format(attDtId=cleaned))


@tool
def fetchEmpShortLeavesByDateRange(
    startDate: str,
    endDate: str,
    fullname: str = "",
    empNo: str = "",
    limit: ReadLimit = 250
) -> list:
    """Retrieves short leave application records (leaving time, return time, reason, status) across a date range between startDate and endDate.

    DYNAMIC DATE RANGE GENERATION (startDate and endDate variables):
    - When the user asks for short leaves over a time window (e.g. "short leaves in the last 7 days", "past 14 days", "past month", "short leaves between X and Y"):
      * You (the LLM) must dynamically compute and set BOTH date variables ('startDate' and 'endDate') in YYYY-MM-DD format based on the prompt.

    ARGUMENTS:
    - startDate (str): Beginning of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - endDate (str): End of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - fullname (str, optional): Employee full or partial name (e.g. 'Rasika').
    - empNo (str/int, optional): Employee Number (staff ID).
    - limit (int, optional): Max records to return (default 250).

    RETURNS:
    List of short leave records with fields: empNo, date, fromTime (leaving time), toTime (return time), reason, status.
    Maps to /api/attendance/employee/{empNo} and /api/emp-short-leaves/employee/{empNo}.
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
                return [{"status": "ambiguous", "message": f"Found multiple employees matching '{clean_name}'. Please specify by employee number (empNo)."}]
        except Exception:
            pass

    if target_empno:
        # Cross-reference with attendance where attendanceType is 'Short Leave'
        att_recs = make_request(f"/api/attendance/employee/{target_empno}")
        short_leaves = []
        if isinstance(att_recs, list) and att_recs:
            for a in att_recs:
                if not isinstance(a, dict):
                    continue
                d = str(a.get("date") or "")
                att_type = str(a.get("attendanceType") or "")
                if s_dt <= d <= e_dt and "Short Leave" in att_type:
                    short_leaves.append({
                        "empNo": target_empno,
                        "date": d,
                        "attendanceType": att_type,
                        "inTime": a.get("inTime"),
                        "outTime": a.get("outTime")
                    })
            if short_leaves:
                sorted_leaves = sorted(short_leaves, key=lambda x: str(x.get("date", "")), reverse=True)
                return sorted_leaves[:limit] if limit else sorted_leaves

        res = make_request(f"/api/emp-short-leaves/employee/{target_empno}")
        if isinstance(res, list) and res:
            return res[:limit] if limit else res

    return [{"notice": f"No short leave records found between {s_dt} and {e_dt}."}]

