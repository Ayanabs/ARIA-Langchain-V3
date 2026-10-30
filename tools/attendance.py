import os
import logging
from typing import Any, Dict, List, Optional
from aria_agent.schemas.retrieval import ReadLimit, OptionalReadLimit
from datetime import timedelta, date, datetime, time
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

logger = logging.getLogger(__name__)


@tool
def fetchAllActualAttendanceByEmployee(empNo: str) -> list:
    """Retrieves the complete, full historical clock-in (entering) and clock-out (leaving) attendance logs for a specific employee (all records, complete history).
    Arguments:
    - empNo (str/int): Employee Number (staff ID).
    Database & JSON fields returned per record:
    - empNo (int): Employee Number.
    - date (str): Attendance calendar date (Format: YYYY-MM-DD).
    - inTime / entering_time (str): Clock-in / arrival timestamp (HH:MM:SS).
    - outTime / leaving_time (str): Clock-out / departure timestamp (HH:MM:SS).
    - attendanceType (str): Attendance status ('Full Day Present', 'Full Day Leave', 'Half Day Leave', 'Short Leave', etc.).
    SCHEMA RELATION & RELATED TOOLS:
    - If attendance status indicates leave ('Full Day Leave', 'Half Day Leave'), call 'fetchEmpLeavesByEmployee' to retrieve approved leave applications, categories (annual, casual, medical), and reasons.
    - If attendance status indicates 'Short Leave', call 'fetchEmpShortLeavesByEmployee' to inspect the exact approved short leave hours and reasons.
    Use when asked: 'Show all attendance for employee X', 'I need the full attendance of X', 'All attendance logs', 'Complete attendance history for X', or 'Full attendance records'.
    Maps to GET /api/attendance/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return [{"error": f"Invalid employee number format: {empNo}"}]

    res = make_request(f"/api/attendance/employee/{cleaned}")
    return res if isinstance(res, list) else []


@tool
def fetchActualAttendanceByEmployee(empNo: str, limit: OptionalReadLimit = None) -> list:
    """Retrieves actual historical clock-in (entering) and clock-out (leaving) attendance logs for an employee.
    Arguments:
    - empNo (str/int): Employee Number (staff ID).
    - limit (int, optional): Number of attendance logs to return.
      * Set limit=1 when asked for the latest, most recent, or last attendance record.
      * If asked for full or all attendance records, omit limit or call 'fetchAllActualAttendanceByEmployee'.
    Database & JSON fields returned per record:
    - empNo (int): Employee Number (staff ID).
    - date (str): Attendance calendar date (Format: YYYY-MM-DD).
    - inTime / entering_time (str): Actual recorded clock-in time (Format: HH:MM:SS).
    - outTime / leaving_time (str): Actual recorded clock-out time (Format: HH:MM:SS).
    - attendanceType (str): Attendance status ('Full Day Present', 'Full Day Leave', 'Half Day Leave', 'Short Leave', etc.).
    SCHEMA RELATION & RELATED TOOLS:
    - If attendance status indicates leave ('Full Day Leave', 'Half Day Leave'), call 'fetchEmpLeavesByEmployee' to retrieve approved leave applications, categories (annual, casual, medical), and reasons.
    - If attendance status indicates 'Short Leave', call 'fetchEmpShortLeavesByEmployee' to inspect the exact approved short leave hours and reasons.
    Use when asked: 'What time did employee enter/leave?', 'Show actual attendance for employee X', 'When did employee X clock in/out?', 'Latest attendance record', or 'Full attendance record'.
    Maps to GET /api/attendance/employee/{empNo}/recent (or /api/attendance/employee/{empNo})."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return [{"error": f"Invalid employee number format: {empNo}"}]

    if limit is not None and int(limit) > 0:
        res = make_request(f"/api/attendance/employee/{cleaned}/recent?limit={int(limit)}")
    else:
        res = make_request(f"/api/attendance/employee/{cleaned}")

    return res if isinstance(res, list) else []


def _execute_attendance_date_range(
    startDate: str,
    endDate: str,
    empNo: str = "",
    fullname: str = "",
    limit: OptionalReadLimit = None
) -> list:
    target_empno = clean_id(empNo) if empNo else ""
    records = []

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
            elif len(records) == 0 or (isinstance(emp_res, dict) and "error" in emp_res):
                return [{"error": f"No employee found matching '{clean_name}'. Attendance records can only be retrieved for registered employees."}]
        except Exception as err:
            logger.warning(f"[AttendanceTool] Error resolving employee name '{clean_name}': {err}")

    s_dt = str(startDate).strip() if startDate else ""
    e_dt = str(endDate).strip() if endDate else ""
    if not s_dt or not e_dt:
        if target_empno:
            logger.info(f"[AttendanceTool] Date range omitted for employee '{target_empno}' — falling back to complete attendance records.")
            return fetchActualAttendanceByEmployee(target_empno, limit=limit)
        return [{"error": "Both startDate and endDate (YYYY-MM-DD) are required"}]

    if target_empno:
        # Resolve employee metadata for enrichment
        emp_meta = None
        if records and isinstance(records[0], dict) and records[0].get("fullname"):
            emp_meta = records[0]
        else:
            try:
                emp_lookup = make_request(f"/api/employees/empno/{target_empno}")
                if isinstance(emp_lookup, dict) and emp_lookup.get("fullname"):
                    emp_meta = emp_lookup
            except Exception:
                pass

        emp_fn = emp_meta.get("fullname") if emp_meta else None
        emp_desig = None
        emp_div = None
        if emp_meta:
            d_v = emp_meta.get("designation")
            emp_desig = d_v if isinstance(d_v, str) else (d_v.get("designation") if isinstance(d_v, dict) else None)
            div_v = emp_meta.get("division")
            emp_div = div_v if isinstance(div_v, str) else (div_v.get("division") if isinstance(div_v, dict) else None)

        appt_date = None
        if emp_meta:
            raw_appt = (
                emp_meta.get("dateofappoinment")
                or emp_meta.get("appointmentDate")
                or emp_meta.get("appointment_date")
                or emp_meta.get("dateOfAppointment")
            )
            if raw_appt:
                appt_date = str(raw_appt).split("T")[0].strip()

        def _build_empty_range_notice(valid_recs: list) -> str:
            name_str = f" for {emp_fn} (Employee No: {target_empno})" if emp_fn else f" for employee {target_empno}"
            msg_parts = [f"No attendance records found between {s_dt} and {e_dt}{name_str}."]
            if appt_date:
                if e_dt and str(e_dt) < str(appt_date):
                    msg_parts.append(
                        f"The employee was appointed to the institute on {appt_date}, "
                        f"meaning they were not yet in service during the requested period {s_dt} to {e_dt}."
                    )
                else:
                    msg_parts.append(f"The employee's official appointment date at the institute is {appt_date}.")
            if valid_recs:
                sorted_all = sorted(valid_recs, key=lambda x: str(x.get("date", "")), reverse=True)
                latest_date = sorted_all[0].get("date")
                earliest_date = sorted_all[-1].get("date")
                msg_parts.append(f"Available recorded attendance in the system spans from {earliest_date} to {latest_date}.")
            return " ".join(msg_parts)

        # 1. Primary: Spring Boot REST API
        res = make_request(f"/api/attendance/employee/{target_empno}")
        if isinstance(res, list) and res:
            filtered = [
                r for r in res
                if isinstance(r, dict) and r.get("date") and s_dt <= str(r.get("date")) <= e_dt
            ]
            if filtered:
                if emp_fn or emp_desig or emp_div:
                    for r in filtered:
                        if emp_fn and "fullname" not in r:
                            r["fullname"] = emp_fn
                        if emp_desig and "designation" not in r:
                            r["designation"] = emp_desig
                        if emp_div and "division" not in r:
                            r["division"] = emp_div
                sorted_records = sorted(filtered, key=lambda x: str(x.get("date", "")), reverse=True)
                return sorted_records[:limit] if limit else sorted_records

            # Fallback: if range yielded 0 records (e.g. user passed modern dates for historical data), return latest available
            valid_records = [r for r in res if isinstance(r, dict) and r.get("date")]
            notice_text = _build_empty_range_notice(valid_records)
            payload: Dict[str, Any] = {"notice": notice_text}
            if emp_fn:
                payload["fullname"] = emp_fn
            if target_empno:
                payload["empNo"] = target_empno
            if valid_records:
                sorted_all = sorted(valid_records, key=lambda x: str(x.get("date", "")), reverse=True)
                payload["latest_available_records"] = sorted_all[: (limit or 7)]
            return [payload]


        notice_text = _build_empty_range_notice([])
        payload = {"notice": notice_text}
        if emp_fn:
            payload["fullname"] = emp_fn
        if target_empno:
            payload["empNo"] = target_empno
        return [payload]

    # General Institution-wide Attendance across all employees in [s_dt, e_dt]
    try:
        from datetime import datetime, timedelta
        start_d = datetime.strptime(s_dt, "%Y-%m-%d").date()
        end_d = datetime.strptime(e_dt, "%Y-%m-%d").date()
        delta = (end_d - start_d).days
        if 0 <= delta <= 14:
            all_recs = []
            curr = end_d
            while curr >= start_d:
                dt_str = curr.strftime("%Y-%m-%d")
                daily_res = make_request(f"/api/attendance/date/{dt_str}")
                if isinstance(daily_res, list) and daily_res:
                    all_recs.extend(daily_res)
                curr -= timedelta(days=1)
            if all_recs:
                return all_recs[:limit] if limit else all_recs
    except Exception as general_err:
        logger.debug(f"[AttendanceTool] Multi-date query error: {general_err}")

    return [{"notice": f"No institution-wide attendance records found between {s_dt} and {e_dt}."}]


@tool
def fetchActualAttendanceByDateRange(
    startDate: str = "",
    endDate: str = "",
    fullname: str = "",
    empNo: str = "",
    limit: OptionalReadLimit = None
) -> list:
    """Retrieves clock-in (arrival) and clock-out (departure) attendance logs across a calendar date range between startDate and endDate.

    DYNAMIC DATE RANGE GENERATION (startDate and endDate variables):
    - When the user asks for a relative attendance time window (such as "attendance within 7 days", "last 7 days", "records of the latest 7 days", "past week", "past 30 days", "past month"):
      * You (the LLM) must dynamically compute and set BOTH date variables ('startDate' and 'endDate') in YYYY-MM-DD format based on the prompt and conversation context:
        1. Historical Anchor: If an earlier conversation turn established a latest known historical attendance date for the person (for example: "Rasika's latest attendance record is from December 31, 2021"), set 'endDate'="2021-12-31" and calculate 'startDate' by subtracting the requested number of days (e.g. 7 days prior -> "2021-12-24").
        2. Current Reference: If no historical anchor is present, calculate 'startDate' and 'endDate' relative to the current date in the Live Dynamic Execution Context (e.g. startDate = today - 7 days, endDate = today).
        3. Calendar Window: If the user provides explicit calendar dates or months (e.g. "between 2021-06-01 and 2021-06-30" or "for October 2021"), populate 'startDate' and 'endDate' directly.

    ARGUMENTS:
    - startDate (str): Beginning of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - endDate (str): End of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - fullname (str, optional): Employee full or partial name (e.g. 'Rasika', 'Rasika Nishanthi Somathilake'). If provided, automatically resolves their staff record and returns their attendance logs.
    - empNo (str/int, optional): Employee Number (staff ID, e.g. '107').
    - limit (int, optional): Max records to return.

    RETURNS:
    List of attendance logs with fields:
    - empNo (int): Employee number.
    - date (str): Calendar date (YYYY-MM-DD).
    - inTime (str): Clock-in arrival time (HH:MM:SS).
    - outTime (str): Clock-out departure time (HH:MM:SS).
    - attendanceType (str): Status ('Full Day Present', 'Full Day Leave', 'Half Day Leave', 'Short Leave', etc.).

    Use whenever the user asks for attendance across a time window, date range, or relative days (e.g. 'attendance of Rasika within 7 days', 'latest 7 days of attendance', 'attendance between X and Y', 'past week attendance').
    """
    return _execute_attendance_date_range(startDate, endDate, empNo=empNo, fullname=fullname, limit=limit)


@tool
def fetchActualAttendanceByEmployeeAndDateRange(
    empNo: str = "",
    startDate: str = "",
    endDate: str = "",
    fullname: str = "",
    limit: OptionalReadLimit = None
) -> list:
    """Retrieves actual historical clock-in and clock-out attendance logs for a specific employee across a defined calendar date range [startDate, endDate].

    DYNAMIC DATE RANGE GENERATION:
    - When the user asks for relative dates (e.g. "attendance within 7 days", "last 7 days", "records of the latest 7 days", "past week"):
      * Set 'endDate' to the latest known historical date or current reference date.
      * Set 'startDate' by subtracting the requested number of days from 'endDate'.
      * Format both dates as YYYY-MM-DD.

    ARGUMENTS:
    - empNo (str/int, optional): Employee Number (staff ID).
    - startDate (str): Range start date inclusive (Format: YYYY-MM-DD).
    - endDate (str): Range end date inclusive (Format: YYYY-MM-DD).
    - fullname (str, optional): Employee full or partial name (e.g. 'Rasika').
    - limit (int, optional): Max records to return.

    Returns list of attendance logs with fields: empNo, date, inTime, outTime, attendanceType.
    Use when the user specifies a date range, year range, or month window for an employee's attendance (e.g. 'attendance between 2021-01-01 and 2021-12-31', 'attendance of Rasika for the last 7 days', or 'attendance for October 2021').
    """
    return _execute_attendance_date_range(startDate, endDate, empNo=empNo, fullname=fullname, limit=limit)


@tool
def fetchActualAttendanceByEmployeeAndDate(empNo: str, date: str) -> dict:
    """Retrieves the exact entering (in-time) and leaving (out-time) timestamps for an employee on a specific calendar date.
    Arguments:
    - empNo (str/int): Employee Number.
    - date (str): Calendar date (Format: YYYY-MM-DD).
    Returns:
    - empNo, date, inTime (entering time), outTime (leaving time), attendanceType.
    SCHEMA RELATION & RELATED TOOLS:
    - If the returned record indicates leave ('Full Day Leave', 'Half Day Leave', 'Short Leave'), call 'fetchEmpLeavesByEmployee' or 'fetchEmpShortLeavesByEmployee' to verify approved leave reasons and time windows for that date.
    Use when asked about employee arrival and departure on a specific date (e.g. 'What time did employee 324 leave on 2021-12-31?').
    Maps to GET /api/attendance/employee/{empNo}/date/{date}."""
    cleaned = clean_id(empNo)
    if not cleaned or not date or not str(date).strip():
        return {"error": "Both empNo and date (YYYY-MM-DD) are required"}

    dt_str = str(date).strip()

    res = make_request(f"/api/attendance/employee/{cleaned}/date/{dt_str}")
    if isinstance(res, dict) and "error" not in res and res:
        return res

    return {"error": f"No attendance record found for employee {empNo} on date {dt_str}"}


@tool
def fetchActualAttendanceByDate(date: str, limit: ReadLimit = 250) -> list:
    """Retrieves all employee clock-in (entering) and clock-out (leaving) records on a specific date.
    Arguments:
    - date (str): Calendar date (Format: YYYY-MM-DD).
    - limit (int, optional): Max number of staff records to return (default 250).
    Maps to GET /api/attendance/date/{date}."""
    if not date or not str(date).strip():
        return [{"error": "Date cannot be empty (Format: YYYY-MM-DD)"}]

    dt_str = str(date).strip()

    res = make_request(f"/api/attendance/date/{dt_str}")
    if isinstance(res, list) and res:
        return res[:limit] if limit else res

    return res if isinstance(res, list) else []
