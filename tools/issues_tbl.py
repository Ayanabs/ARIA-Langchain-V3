from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllIssues() -> list:
    """Retrieves electronic timecard attendance discrepancy issues for all employees from GET /api/issues.
    Database and JSON fields returned per record:
    - AttDtId (int) [FOREIGN KEY]: Foreign key linking to attendance date record ID.
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - Desc / description (str): Attendance issue explanation (e.g. 'Missing In Punch', 'Missing Out Punch', 'Late Arrival', 'Unauthorized Absence').
    - issue_type (str): Issue type code ('In', 'Out', 'Late', 'Absence').
    Maps to GET /api/issues."""
    return make_request("/api/issues")

@tool
def fetchIssuesByEmpNo(empNo: str) -> list:
    """Retrieves timecard attendance discrepancy issues for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: AttDtId [FK], EmpNo [FK], Desc (issue description), issue_type.
    Maps to GET /api/issues/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/issues/employee/{cleaned}")

@tool
def fetchIssuesByType(issueType: str) -> list:
    """Retrieves attendance issues filtered by issue type ('In' for missing in-punch, 'Out' for missing out-punch, 'Late').
    Maps to GET /api/issues/type/{issueType}."""
    if not issueType or not str(issueType).strip():
        return {"error": "Issue type cannot be empty"}
    return make_request(f"/api/issues/type/{str(issueType).strip()}")


@tool
def fetchIssueByAttDtId(attDtId: str) -> list:
    """Retrieves issue record by attendance date ID. Maps to GET /api/issues/{attDtId}."""
    cleaned = clean_id(attDtId) if isinstance(attDtId, (int, str)) else str(attDtId)
    if not cleaned:
        return {"error": f"Invalid attDtId format: {attDtId}"}
    return make_request(f"/api/issues/{attDtId}".format(attDtId=cleaned))

