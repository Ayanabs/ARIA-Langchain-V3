from typing import Any
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllLeaveActing() -> list:
    """Retrieves all leave acting cover arrangements across the entire organisation.
    Each record contains: Lv_Act_ID, Emp_No (absent employee), Act_Emp_No (substitute/covering officer),
    Leave_Start_Date, Leave_End_Date, and status.
    Maps to /api/leave-acting."""
    return make_request("/api/leave-acting")

@tool
def fetchLeaveActingByEmployee(empNo: str) -> list:
    """Retrieves acting arrangement records for an employee taking leave (who acted on their behalf while they were absent).
    Returns: empNo (absent employee), actingEmpNo (substitute/covering officer), leaveStartDate, leaveEndDate, status, dutiesAssigned.
    Use when asked who acted for or covered duties for an employee while on leave.
    Maps to /api/leave-acting/employee/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {
            "error": f"Invalid employee number format: {empNo}"
        }

    return make_request(
        f"/api/leave-acting/employee/{cleaned}"
    )

@tool
def fetchLeaveActingByActingEmployee(actEmpNo: str) -> list:
    """Retrieves leave acting cover records where a specific employee (actEmpNo) acted or covered duties for another employee on leave.
    Returns: actEmpNo, absentEmpNo, leaveStartDate, leaveEndDate, status.
    Use when asked which employees or duties a person covered as an acting officer.
    Maps to /api/leave-acting/acting-employee/{actEmpNo}."""
    cleaned = clean_id(actEmpNo)

    if not cleaned:
        return {
            "error": f"Invalid acting employee number format: {actEmpNo}"
        }

    return make_request(
        f"/api/leave-acting/acting-employee/{cleaned}"
    )

@tool
def fetchLeaveActingByEmpNo(empNo: str) -> Any:
    """Retrieves leave acting cover records for an employee by empNo. Maps to /api/leave-acting/employee/{empNo}."""
    return fetchLeaveActingByEmployee.func(empNo)
