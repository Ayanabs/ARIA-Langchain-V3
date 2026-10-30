from typing import Any, Dict, List
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id


def _format_res(res: Any) -> list:
    if isinstance(res, Exception) or (isinstance(res, dict) and "error" in res):
        return []
    return res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])


@tool
def fetchEmployeeLeaveSummary(empNo: str) -> Dict[str, Any]:
    """Composite domain router tool.
    Retrieves complete leave records summary, short leaves (with leaving and return times), and overseas leaves
    for an employee by empNo concurrently in a single call.
    Use when asked about an employee's leave balance, leave records, short leaves, or leave history.
    Maps to /api/emp-leaves/employee/{empNo}, /api/emp-short-leaves/employee/{empNo}, and /api/emp-leaves/overseas.
    """
    cleaned = clean_id(empNo) or str(empNo).strip()

    # Query Spring Boot endpoints with backwards-compatible fallback paths
    emp_leaves = make_request(f"/api/emp-leaves/employee/{cleaned}")
    if isinstance(emp_leaves, dict) and "error" in emp_leaves:
        emp_leaves = make_request(f"/api/emp-lv-tbl/employee/{cleaned}")

    short_leaves = make_request(f"/api/emp-short-leaves/employee/{cleaned}")
    if isinstance(short_leaves, dict) and "error" in short_leaves:
        short_leaves = make_request(f"/api/emp-slv-tbl/employee/{cleaned}")

    overseas_leaves = make_request("/api/emp-leaves/overseas")
    if isinstance(overseas_leaves, dict) and "error" in overseas_leaves:
        overseas_leaves = make_request("/api/emp-lv-tbl/overseas")

    all_leaves = _format_res(emp_leaves)
    all_short_leaves = _format_res(short_leaves)
    raw_overseas = _format_res(overseas_leaves)

    # Dynamically filter overseas leaves specifically for this employee
    filtered_overseas = [
        r for r in raw_overseas
        if isinstance(r, dict) and str(r.get("empNo") or r.get("empno") or r.get("emp_no") or "").strip() == cleaned
    ]

    # Dynamically compute aggregate metrics across leaves
    total_days = 0.0
    leaves_by_type_count: Dict[str, int] = {}
    leaves_by_type_days: Dict[str, float] = {}

    for r in all_leaves:
        if isinstance(r, dict):
            day_val = 0.0
            for k in ("noOfDays", "noofdays", "days", "count", "numDays"):
                if k in r and r[k] is not None:
                    try:
                        day_val = float(r[k])
                        break
                    except (ValueError, TypeError):
                        pass
            total_days += day_val

            type_key = None
            for k in ("leaveTypeId", "leavetypeid", "typeId", "leaveType", "type", "slvType"):
                if k in r and r[k] is not None:
                    type_key = str(r[k])
                    break
            if type_key is not None:
                leaves_by_type_count[type_key] = leaves_by_type_count.get(type_key, 0) + 1
                leaves_by_type_days[type_key] = leaves_by_type_days.get(type_key, 0.0) + day_val

    summary = {
        "total_leave_records": len(all_leaves),
        "total_leave_days_taken": round(total_days, 1),
        "total_short_leaves_recorded": len(all_short_leaves),
        "total_overseas_leaves": len(filtered_overseas),
        "leave_count_by_type_id": leaves_by_type_count,
        "leave_days_by_type_id": {k: round(v, 1) for k, v in leaves_by_type_days.items()}
    }

    # Cap raw record sample to prevent context bloat (25k+ tokens -> ~500 tokens)
    sample_leaves = all_leaves[:15] if len(all_leaves) > 15 else all_leaves
    sample_short_leaves = all_short_leaves[:15] if len(all_short_leaves) > 15 else all_short_leaves

    return {
        "empNo": cleaned,
        "summary": summary,
        "leaves": sample_leaves,
        "total_leaves_count": len(all_leaves),
        "short_leaves": sample_short_leaves,
        "total_short_leaves_count": len(all_short_leaves),
        "overseas_leaves": filtered_overseas
    }


@tool
def fetchEmployeeWorkSchedule(empNo: str) -> Dict[str, Any]:
    """Retrieves official work schedule, daily entry time, and leaving time for an employee by employee number (empNo).
    Resolves staff category schedule:
    - entry_time: Scheduled morning arrival / in-time (Format: HH:MM:SS, e.g. '08:30:00').
    - leaving_time: Scheduled evening departure / leaving time (Format: HH:MM, e.g. '16:15').
    - late_threshold: Grace time limit before being recorded as a late arrival.
    - adjustment_time: Shift adjustment time threshold.
    Use when asked: 'What is my leaving time?', 'When does employee X leave?', 'What time does employee arrive and leave?', or 'What is employee work schedule?'.
    Maps to GET /api/employees/empno/{empNo} and GET /api/categories/{categorycode}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    emp = make_request(f"/api/employees/empno/{cleaned}")
    if isinstance(emp, list) and emp:
        emp = emp[0]

    if not isinstance(emp, dict) or "error" in emp:
        return {"error": f"Employee {empNo} not found or request failed."}

    category_code = emp.get("categorycode")
    cat_data = None
    if category_code is not None:
        cat_data = make_request(f"/api/categories/{category_code}")
        if not isinstance(cat_data, dict) or "error" in cat_data:
            cat_data = make_request(f"/api/categories/code/{category_code}")

    if isinstance(cat_data, list) and cat_data:
        cat_data = cat_data[0]

    leaving_time = None
    entry_time = None
    late_threshold = None
    adjustment_time = None
    category_name = None

    if isinstance(cat_data, dict) and "error" not in cat_data:
        category_name = cat_data.get("category")
        entry_time = cat_data.get("intime")
        out_h = cat_data.get("outtimeh")
        out_m = cat_data.get("outtimem", 0)
        if out_h is not None:
            try:
                leaving_time = f"{int(out_h):02d}:{int(out_m or 0):02d}"
            except (ValueError, TypeError):
                leaving_time = f"{out_h}:{out_m}"
        late_threshold = cat_data.get("latetime")
        adjustment_time = cat_data.get("adjesttime")

    return {
        "empNo": cleaned,
        "fullname": emp.get("fullname"),
        "category": category_name,
        "categoryCode": category_code,
        "entry_time": entry_time,
        "leaving_time": leaving_time,
        "late_threshold": late_threshold,
        "adjustment_time": adjustment_time
    }


@tool
def fetchEmployeeLeavingSummary(empNo: str) -> Dict[str, Any]:
    """Composite tool providing comprehensive leaving and departure information for an employee.
    Consolidates:
    1. Regular shift work schedule: Entry time ('intime') and regular leaving time ('leaving_time').
    2. Short leave records: Approved temporary departure (leaving) times ('fromTime') and return (entry) times ('toTime').
    3. Approved leave history: Full-day and half-day taken leaves.
    4. Overseas leave approvals.
    Use when asked about employee leaving times, departure times, short leaves, or leave history.
    """
    cleaned = clean_id(empNo) or str(empNo).strip()
    schedule = fetchEmployeeWorkSchedule.func(cleaned)
    leave_summary = fetchEmployeeLeaveSummary.func(cleaned)

    formatted_short_leaves = []
    for sl in leave_summary.get("short_leaves", []):
        if isinstance(sl, dict):
            item = dict(sl)
            from_time = sl.get("fromTime") or sl.get("from_time") or sl.get("startTime") or sl.get("slv_time_from")
            to_time = sl.get("toTime") or sl.get("to_time") or sl.get("endTime") or sl.get("slv_time_to")
            if from_time:
                item["leaving_time"] = str(from_time)
            if to_time:
                item["entry_return_time"] = str(to_time)
            formatted_short_leaves.append(item)
        else:
            formatted_short_leaves.append(sl)

    fullname = schedule.get("fullname") if isinstance(schedule, dict) else None

    recent_att = []
    try:
        from aria_agent.tools.attendance import fetchActualAttendanceByEmployee
        recent_att = fetchActualAttendanceByEmployee.func(cleaned, limit=5)
    except Exception:
        pass

    return {
        "empNo": cleaned,
        "fullname": fullname,
        "work_schedule": {
            "category": schedule.get("category") if isinstance(schedule, dict) else None,
            "entry_time": schedule.get("entry_time") if isinstance(schedule, dict) else None,
            "leaving_time": schedule.get("leaving_time") if isinstance(schedule, dict) else None,
            "late_threshold": schedule.get("late_threshold") if isinstance(schedule, dict) else None,
        },
        "recent_actual_attendance": recent_att,
        "short_leaves": formatted_short_leaves,
        "leaves": leave_summary.get("leaves", []),
        "overseas_leaves": leave_summary.get("overseas_leaves", [])
    }


