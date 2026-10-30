import asyncio
from typing import Any, Dict, Optional
from langchain_core.tools import tool
from aria_agent.http.client import make_request, make_graphql_query, clean_id


@tool
def fetchUnifiedEmployee360(empNo: str = "", fullname: str = "") -> Dict[str, Any]:
    """Single-turn 360-degree consolidated employee router tool.
    Retrieves complete employee profile, qualifications (higher education, G.C.E. A/L, G.C.E. O/L), 
    salary & allowance details, official HR details, personal details, family dependents, and active projects in a single GraphQL HTTP POST request (or parallel REST fallback).
    Accepts either an employee number (empNo) OR an employee full name (fullname). 
    If a full name is provided, it automatically resolves the empNo first. If multiple matching
    employees exist with the same name, it returns a clarification list for the user to choose.
    Use when asked for an employee's full profile, 360 view, complete details, salary, qualifications, or background.
    """
    target_empno = clean_id(empNo) if empNo else ""

    # 1. If empNo was not provided, resolve it automatically from fullname in turn 1
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
        return {"error": "Please provide a valid employee number (empNo) or employee full name (fullname)."}

    # 2. Attempt single GraphQL POST request to fetch all 9 employee domains in 1 HTTP round-trip
    gql_query = """
    query GetUnifiedEmployee360($empNo: String!) {
        employee360(empNo: $empNo) {
            empNo
            masterRecord { empno fullname designation divCode }
            officialDetails { email joiningDate desigCode divCode }
            personalDetails { nic dob phone address }
            dependents { name relationship dob }
            higherEducation { empNo degree institute year grade }
            gceAlQualifications { subject grade year }
            gceOlQualifications { subject grade year }
            salaryDetails { basicSalary netSalary allowances }
            activeProjects { projectName role status }
        }
    }
    """
    gql_res = make_graphql_query(gql_query, {"empNo": target_empno}, "GetUnifiedEmployee360")
    if isinstance(gql_res, dict) and "employee360" in gql_res:
        data = gql_res["employee360"] or {}
        return {
            "empNo": target_empno,
            "master_record": data.get("masterRecord") or [],
            "official_details": data.get("officialDetails") or [],
            "personal_details": data.get("personalDetails") or [],
            "dependents": data.get("dependents") or [],
            "higher_education": data.get("higherEducation") or [],
            "gce_al_qualifications": data.get("gceAlQualifications") or [],
            "gce_ol_qualifications": data.get("gceOlQualifications") or [],
            "salary_details": data.get("salaryDetails") or [],
            "active_projects": data.get("activeProjects") or []
        }

    # 3. REST Fallback
    master_res = make_request(f"/api/employees/empno/{target_empno}")
    official_res = make_request(f"/api/hr-official-details/employee/{target_empno}")
    personal_res = make_request(f"/api/hr-personal-details/employee/{target_empno}")
    dep_res = make_request(f"/api/hr-dep-details/employee/{target_empno}")
    hiedu_res = make_request(f"/api/hr-higher-edu-details/employee/{target_empno}")
    al_res = make_request(f"/api/hr-q-al/employee/{target_empno}")
    ol_res = make_request(f"/api/hr-q-ol/employee/{target_empno}")
    salary_res = make_request(f"/api/hr-salary-table/employee/{target_empno}")
    project_res = make_request(f"/api/hr-projects/employee/{target_empno}")

    def _clean(res):
        if isinstance(res, Exception) or (isinstance(res, dict) and "error" in res):
            return []
        return res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])

    master_clean = _clean(master_res)
    official_clean = _clean(official_res)
    personal_clean = _clean(personal_res)
    dep_clean = _clean(dep_res)
    hiedu_clean = _clean(hiedu_res)
    al_clean = _clean(al_res)
    ol_clean = _clean(ol_res)
    salary_clean = _clean(salary_res)
    project_clean = _clean(project_res)

    if not any([master_clean, official_clean, personal_clean, dep_clean, hiedu_clean, al_clean, ol_clean, salary_clean, project_clean]):
        return []

    return {
        "empNo": target_empno,
        "master_record": master_clean,
        "official_details": official_clean,
        "personal_details": personal_clean,
        "dependents": dep_clean,
        "higher_education": hiedu_clean,
        "gce_al_qualifications": al_clean,
        "gce_ol_qualifications": ol_clean,
        "salary_details": salary_clean,
        "active_projects": project_clean
    }
