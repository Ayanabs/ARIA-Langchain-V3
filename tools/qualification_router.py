import asyncio
from typing import Any, Dict
from langchain_core.tools import tool
from aria_agent.http.client import make_request, make_graphql_query, clean_id


@tool
def fetchEmployeeQualificationSummary(empNo: str = "", fullname: str = "") -> Dict[str, Any]:
    """Composite domain router tool.
    Retrieves full academic background (Higher Education degrees/diplomas, G.C.E. A/L exam results, and G.C.E. O/L exam results)
    for an employee by empNo OR employee full name (fullname) in a single request via GraphQL (or parallel REST fallback).
    Accepts either an employee number (empNo) OR an employee full name (fullname).
    If a full name is provided, it automatically resolves the empNo first. If multiple matching
    employees exist with the same name, it returns a clarification list for the user to choose.
    Always use this tool when asked about an employee's qualifications, education, degrees, or academic records.
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

    # 1. Attempt single-turn GraphQL query to minimize HTTP requests
    gql_query = """
    query GetEmployeeQualifications($empNo: String!) {
        employeeQualifications(empNo: $empNo) {
            empNo
            higherEducation { id empNo subEduType higherEduLevel description }
            gceAl { hrQAlid empNo aLIndex aLSubNo aLSubName aLSubGrade aLYear }
            gceOl { hrOlQid empNo oLIndex oLSubNo oLSubName oLSubGrade oLYear }
        }
    }
    """
    gql_res = make_graphql_query(gql_query, {"empNo": target_empno}, "GetEmployeeQualifications")
    if isinstance(gql_res, dict) and "employeeQualifications" in gql_res:
        data = gql_res["employeeQualifications"] or {}
        return {
            "empNo": target_empno,
            "higher_education": data.get("higherEducation") or [],
            "gce_al": data.get("gceAl") or [],
            "gce_ol": data.get("gceOl") or []
        }

    # 2. Single-turn Composite REST Summary Endpoint
    summary_res = make_request(f"/api/qualifications/summary/employee/{target_empno}")
    if isinstance(summary_res, dict) and "empNo" in summary_res:
        return summary_res

    # 3. REST Fallback
    higher_edu = make_request(f"/api/hr-higher-edu-details/employee/{target_empno}")
    al_results = make_request(f"/api/hr-q-al/employee/{target_empno}")
    ol_results = make_request(f"/api/hr-q-ol/employee/{target_empno}")

    def _format_res(res):
        if isinstance(res, Exception) or (isinstance(res, dict) and "error" in res):
            return []
        return res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])

    return {
        "empNo": target_empno,
        "higher_education": _format_res(higher_edu),
        "gce_al": _format_res(al_results),
        "gce_ol": _format_res(ol_results)
    }

if hasattr(fetchEmployeeQualificationSummary, "func") and fetchEmployeeQualificationSummary.func:
    fetchEmployeeQualificationSummary.func.composite_endpoints = [
        "/api/hr-higher-edu-details",
        "/api/hr-q-al",
        "/api/hr-q-ol",
        "/api/hr-q-hi-edu",
        "/api/qualifications"
    ]
