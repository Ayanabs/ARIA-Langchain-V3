import asyncio
from typing import Any, Dict
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id


@tool
def fetchEmployeeFullProfileSummary(empNo: str = "", fullname: str = "") -> Dict[str, Any]:
    """Composite domain router tool.
    Retrieves complete employee profile, including official HR details (appointment, retirement, status),
    personal identity details (DOB, NIC, gender, address), and family dependents (spouse, children)
    for an employee by empNo OR employee full name (fullname) in a single request.
    Use when asked about an employee's full profile, official details, personal details, or dependents.
    """
    target_empno = clean_id(empNo) if empNo else ""

    if not target_empno and fullname and str(fullname).strip():
        try:
            emp_res = make_request(f"/api/employees/fullname/{str(fullname).strip()}")
            records = emp_res if isinstance(emp_res, list) else ([emp_res] if isinstance(emp_res, dict) else [])
            if len(records) > 1:
                matches = []
                for rec in records:
                    if isinstance(rec, dict):
                        from aria_agent.utils.data import extract_record_id, extract_record_name, extract_empno_from_dict
                        matches.append({
                            "empNo": extract_empno_from_dict(rec) or extract_record_id(rec),
                            "fullname": extract_record_name(rec) or fullname,
                            "designation": rec.get("designation") or rec.get("desigCode") or "N/A",
                            "division": rec.get("division") or rec.get("divCode") or "N/A"
                        })
                return {
                    "status": "ambiguous",
                    "message": f"Found {len(records)} employees matching '{fullname}'. Please ask the user to clarify which employee they want by empNo:",
                    "matching_employees": matches
                }
            elif len(records) == 1 and isinstance(records[0], dict):
                e_no = records[0].get("empno") or records[0].get("empNo") or records[0].get("emp_no")
                if e_no:
                    target_empno = clean_id(str(e_no))
        except Exception as err:
            return {"error": f"Failed to resolve employee name '{fullname}': {str(err)}"}

    if not target_empno:
        return {"error": "Please provide a valid employee number (empNo) or full name (fullname)."}

    emp_record = make_request(f"/api/employees/empno/{target_empno}")
    if isinstance(emp_record, dict) and "error" in emp_record:
        return {"error": f"Employee with empNo '{target_empno}' not found in the employee directory."}

    official_res = make_request(f"/api/hr-official-details/employee/{target_empno}")
    personal_res = make_request(f"/api/hr-personal-details/employee/{target_empno}")
    dep_res = make_request(f"/api/hr-dep-details/employee/{target_empno}")

    def _format_res(res):
        if isinstance(res, Exception) or (isinstance(res, dict) and "error" in res):
            return []
        return res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])

    return {
        "empNo": target_empno,
        "employee": emp_record if isinstance(emp_record, dict) and "error" not in emp_record else None,
        "official_details": _format_res(official_res),
        "personal_details": _format_res(personal_res),
        "dependents": _format_res(dep_res)
    }
