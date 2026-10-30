from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrProjectDetails() -> list:
    """Retrieves detailed HR project activity specifications from GET /api/hr-project-details.
    Database and JSON fields returned per record:
    - serial_no (int): Primary key row identifier.
    - pname (str): Full project title/name.
    - apnumber / apcode (str): Approval/accounting code.
    - startdate (str): Project commencement date (Format: YYYY-MM-DD).
    - enddate (str): Target completion date (Format: YYYY-MM-DD).
    - ptype (str) [FOREIGN KEY]: Project classification type (linking to 'hr_project_types').
    - cname (str): Client or sponsoring organization name.
    Maps to GET /api/hr-project-details."""
    return make_request("/api/hr-project-details")

@tool
def fetchHrProjectDetailsByProjectName(pname: str) -> list:
    """Retrieves detailed HR project specs filtered by project title/name.
    Maps to GET /api/hr-project-details/project-name/{pname}."""
    if not pname or not str(pname).strip():
        return {"error": "Project name cannot be empty"}
    return make_request(f"/api/hr-project-details/project-name/{quote(pname)}")

@tool
def fetchHrProjectDetailsByApNumber(apnumber: str) -> list:
    """Retrieves detailed HR project specs filtered by approval code (apnumber).
    Maps to GET /api/hr-project-details/ap-number/{apnumber}."""
    if not apnumber or not str(apnumber).strip():
        return {"error": "AP number cannot be empty"}
    return make_request(f"/api/hr-project-details/ap-number/{quote(apnumber)}")

@tool
def fetchHrProjectDetailsByProjectType(ptype: str) -> list:
    """Retrieves detailed HR project specs filtered by project type description (ptype).
    Maps to GET /api/hr-project-details/project-type/{ptype}."""
    if not ptype or not str(ptype).strip():
        return {"error": "Project type cannot be empty"}
    return make_request(f"/api/hr-project-details/project-type/{quote(ptype)}")

@tool
def fetchHrProjectDetailsByCompany(cname: str) -> list:
    """Retrieves detailed HR project specs filtered by client or sponsoring company name (cname).
    Maps to GET /api/hr-project-details/company/{cname}."""
    if not cname or not str(cname).strip():
        return {"error": "Company name cannot be empty"}
    return make_request(f"/api/hr-project-details/company/{quote(cname)}")
