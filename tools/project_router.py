import asyncio
from typing import Any, Dict
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id


@tool
def fetchEmployeeProjectSummary(empNo: str) -> Dict[str, Any]:
    """Composite domain router tool.
    Retrieves project assignments, project details, and project roles for an employee by empNo concurrently.
    Use when asked about an employee's projects, project allocations, project involvements, or project history.
    Maps to /api/hr-projects/employee/{empNo} and /api/hr-project-details.
    """
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    hr_projects = make_request(f"/api/hr-projects/employee/{cleaned}")
    project_details = make_request("/api/hr-project-details")

    def _format_res(res):
        if isinstance(res, Exception) or (isinstance(res, dict) and "error" in res):
            return []
        return res if isinstance(res, list) else ([res] if isinstance(res, dict) else [])

    emp_projects = _format_res(hr_projects)
    if not emp_projects:
        return {
            "empNo": cleaned,
            "employee_projects": [],
            "message": f"No project assignments found for employee #{cleaned} in database records."
        }

    return {
        "empNo": cleaned,
        "employee_projects": emp_projects,
        "all_project_details": _format_res(project_details)
    }
