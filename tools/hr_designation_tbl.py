from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrDesignations() -> list:
    """Retrieves all HR designation records across the organisation from GET /api/hr-designations.
    Database fields returned per record:
    - DesigCode (int) [PRIMARY KEY / FOREIGN KEY]: Unique numeric designation code. Referenced by 'desigcode' in 'hr_official_details' and 'positions_tbl'.
    - Designation (str): Official designation job title (e.g. 'Senior Scientific Officer', 'Management Assistant').
    - SalaryCode (str) [FOREIGN KEY]: Foreign key linking to 'SalaryCode' in 'hr_salary_tbl'.
    - ApCadre (int): Approved cadre count for the designation.
    Maps to GET /api/hr-designations."""
    return make_request("/api/hr-designations")

@tool
def searchHrDesignationsByName(name: str) -> list:
    """Searches HR designations by full or partial job title/name.
    Returns fields including DesigCode [FK], Designation, SalaryCode [FK], ApCadre.
    Maps to GET /api/hr-designations/search?name={name}."""
    if not name or not str(name).strip():
        return {"error": "Designation name cannot be empty"}

    return make_request(f"/api/hr-designations/search?name={quote(name)}")

@tool
def fetchHrDesignationsBySalaryCode(salaryCode: str) -> list:
    """Retrieves all designations associated with a specific salary scale code.
    Arguments & Foreign Key:
    - salaryCode (str) [FOREIGN KEY]: Salary scale code linking to 'SalaryCode' in 'hr_salary_tbl'.
    Maps to GET /api/hr-designations/salary/{salaryCode}."""
    cleaned = clean_id(salaryCode)

    if not cleaned:
        return {"error": f"Invalid salary code format: {salaryCode}"}

    return make_request(f"/api/hr-designations/salary/{cleaned}")
