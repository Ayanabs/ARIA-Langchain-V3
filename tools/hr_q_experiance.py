from typing import Any
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQExperience() -> list:
    """Retrieves all employee prior work experience and employment history records.
    Each record contains: empNo, companyName, designation, startDate, endDate, durationYears, responsibilities.
    Maps to /api/hr-q-experience."""
    return make_request("/api/hr-q-experience")

@tool
def fetchHrQExperienceByEmployeeId(empNo: str) -> list:
    """Retrieves prior employment history and work experience records for an employee by empNo.
    Returns a list of experience entries containing: empNo, companyName/organisation, designation/position held,
    startDate, endDate, totalExperienceYears, duties/responsibilities, and sector.
    Use when asked about an employee's work history, prior experience, previous jobs, former employers, or work background.
    Maps to /api/hr-q-experience/employee/{empNo}."""
    if not empNo or not str(empNo).strip():
        return {"error": "Employee number cannot be empty"}

    return make_request(
        f"/api/hr-q-experience/employee/{str(empNo).strip()}"
    )

@tool
def fetchHrQExperienceByEmpNo(empNo: str) -> Any:
    """Retrieves work experience records for an employee by empNo. Maps to /api/hr-q-experience/employee/{empNo}."""
    return fetchHrQExperienceByEmployeeId.func(empNo)
