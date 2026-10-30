import asyncio
from typing import Any, Dict
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id


@tool
def fetchEmployeeSalarySummary(empNo: str = "", fullname: str = "") -> Dict[str, Any]:
    """Composite domain router tool.
    Retrieves full salary breakdown, allowances, temporary salary info, and salary scale details
    for an employee by empNo OR employee full name (fullname) concurrently in a single call.
    Accepts either an employee number (empNo) OR an employee full name (fullname).
    If a full name is provided, it automatically resolves the empNo first. If multiple matching
    employees exist with the same name, it returns a clarification list for the user to choose.
    Use when asked about an employee's salary, pay, earnings, basic salary, allowances, or scale.
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

    salary_main = make_request(f"/api/hr-salary/employee/{target_empno}")
    temp_salary = make_request(f"/api/hr-temp-salary-info/employee/{target_empno}")
    salary_details = make_request(f"/api/hr-salary-details/employee/{target_empno}")

    def _format_res(res):
        if isinstance(res, Exception) or (isinstance(res, dict) and "error" in res):
            return []
        return res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])

    return {
        "empNo": target_empno,
        "salary_main": _format_res(salary_main),
        "temp_salary_info": _format_res(temp_salary),
        "salary_details": _format_res(salary_details)
    }
