from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrProjects() -> list:
    """Retrieves all HR project records across the organisation from GET /api/hr-projects.
    WARNING: Do NOT use this tool when querying projects of a specific division, department, or unit. Use fetchHrProjectsByDivision or fetchPrProjectsByDivision instead.
    Database fields returned per record:
    - serial_no (int): Primary key row sequence number.
    - code (str): Unique project code (e.g. 'HR/2023/IT/001').
    - pname (str): Full project title/name.
    - div_code (int) [FOREIGN KEY]: Foreign key linking to 'divisioncode' in 'division' / 'hr_division_tbl'. Identifies the managing division.
    - pt_code (int) [FOREIGN KEY]: Foreign key linking to 'pt_code' in 'hr_project_types'. Identifies the project classification type.
    - ptype (str): Human-readable project type name.
    - cname (str): Client or sponsoring organization name.
    - apcode (str): Approval/accounting tracking code.
    - sk_code (str): Technical skill category code.
    - startdate (str): Project start date (YYYY-MM-DD).
    - enddate (str): Project target completion date (YYYY-MM-DD).
    - confirm (str): Confirmation status ('y' = confirmed, 'n' = pending).
    - p_close (str): Closure status ('y' = closed, 'n' = open/active).
    - year (int): Year of project initiation.
    Maps to GET /api/hr-projects."""
    return make_request("/api/hr-projects")

@tool
def fetchHrProjectsByYear(year: str) -> list:
    """Retrieves HR projects filtered by initiation year (e.g. '2023', '2024').
    Returns project fields including div_code [FK], pt_code [FK], code, pname, cname, startdate, enddate.
    Maps to GET /api/hr-projects/year/{year}."""
    cleaned = clean_id(year)

    if not cleaned:
        return {"error": f"Invalid year format: {year}"}

    return make_request(
        f"/api/hr-projects/year/{cleaned}"
    )

@tool
def fetchHrProjectsByDivision(divCode: str = "", divisionCode: str = "", division: str = "") -> list:
    """Retrieves Human Resources (HR) specific internal projects managed by an internal division of the organization.
    WARNING: Do NOT use this tool for external client organizations, sponsors, funders, ministries, or external departments. For external clients or sponsors, use fetchHrProjectsByClient or fetchPrProjectsByClient instead.
    NOTE: For institutional, technical, engineering, software, and research projects of a division, use fetchPrProjectsByDivision instead.
    Arguments & Foreign Key:
    - divCode (str/int) [FOREIGN KEY]: Numeric division code OR division name/abbreviation (e.g. 'IT', 'ITD', 'COM'). Automatically resolves division names.
    Maps to GET /api/hr-projects/division/{divCode}."""
    target_code = divCode or divisionCode or division or ""
    target_str = str(target_code).strip()
    if target_str.isdigit() and len(target_str) == 4 and 1900 <= int(target_str) <= 2100:
        return {"error": f"'{target_str}' is a calendar year, not a division. Use fetchHrProjectsByYear(year='{target_str}') instead."}
    from aria_agent.tools.division import resolve_division_code
    code_int = resolve_division_code(target_code)
    if code_int is not None:
        return make_request(f"/api/hr-projects/division/{code_int}")
    if not target_code or not str(target_code).strip():
        return {"error": "Division code cannot be empty"}

    return make_request(
        f"/api/hr-projects/division/{target_code}"
    )

@tool
def fetchHrProjectsByProjectType(ptCode: str) -> list:
    """Retrieves HR projects filtered strictly by numeric project type code (ptCode).
    WARNING: Do NOT use this tool for department or division queries (use fetchPrProjectsByDivision or fetchHrProjectsByDivision instead).
    Arguments & Foreign Key:
    - ptCode (str/int) [FOREIGN KEY]: Project type classification code (linking to 'pt_code' in 'hr_project_types').
    Maps to GET /api/hr-projects/project-type/{ptCode}."""
    if not ptCode or not str(ptCode).strip():
        return {"error": "Project type code cannot be empty"}

    return make_request(
        f"/api/hr-projects/project-type/{ptCode}"
    )

@tool
def fetchHrProjectsByCode(code: str) -> list:
    """Retrieves HR project details matching a specific unique project code (e.g. 'HR/2023/IT/001').
    Returns fields including div_code [FK], pt_code [FK], pname, cname, startdate, enddate, confirm, p_close.
    Maps to GET /api/hr-projects/code/{code}."""
    if not code or not str(code).strip():
        return {"error": "Project code cannot be empty"}

    return make_request(
        f"/api/hr-projects/code/{quote(code)}"
    )

@tool
def fetchHrProjectsByProjectName(pname: str) -> list:
    """Retrieves HR projects matching a full or partial project title/name.
    Maps to GET /api/hr-projects/name/{pname}."""
    if not pname or not str(pname).strip():
        return {"error": "Project name cannot be empty"}

    return make_request(
        f"/api/hr-projects/name/{quote(pname)}"
    )

@tool
def fetchHrProjectsByApCode(apcode: str) -> list:
    """Retrieves HR projects filtered by approval/accounting code (apcode).
    Maps to GET /api/hr-projects/apcode/{apcode}."""
    if not apcode or not str(apcode).strip():
        return {"error": "AP code cannot be empty"}

    return make_request(
        f"/api/hr-projects/apcode/{quote(apcode)}"
    )

@tool
def fetchHrProjectsByPType(ptype: str) -> list:
    """Retrieves HR projects filtered strictly by official project classification type description/name (ptype, e.g. 'Client based', 'Inhouse', 'Consultancy').
    WARNING: Do NOT use this tool for department or division queries (e.g. do not pass 'IT', 'Information Technology', or division names here; use fetchPrProjectsByDivision or fetchHrProjectsByDivision instead).
    Maps to GET /api/hr-projects/ptype/{ptype}."""
    if not ptype or not str(ptype).strip():
        return {"error": "Project type cannot be empty"}

    return make_request(
        f"/api/hr-projects/ptype/{quote(ptype)}"
    )

@tool
def fetchHrProjectsByClient(cname: str) -> list:
    """Retrieves HR projects funded by, sponsored by, or executed for an external client, sponsor, customer, or partner organization.
    Use this tool whenever the user asks for HR projects related to, funded by, or sponsored by an external client, sponsor, partner institution, ministry, or government department.
    Searches against client/sponsor name (cname). Supports full or partial organization names.
    Maps to GET /api/hr-projects/client/{cname}."""
    if not cname or not str(cname).strip():
        return {"error": "Client name cannot be empty"}

    return make_request(
        f"/api/hr-projects/client/{quote(cname)}"
    )

@tool
def fetchHrProjectsByStatus(confirm: str) -> list:
    """Retrieves HR projects filtered by confirmation status ('y' for confirmed, 'n' for pending).
    Maps to GET /api/hr-projects/status/{confirm}."""
    if not confirm or not str(confirm).strip():
        return {"error": "Status cannot be empty"}

    return make_request(
        f"/api/hr-projects/status/{quote(confirm)}"
    )

@tool
def fetchHrProjectsBySkillCode(skCode: str) -> list:
    """Retrieves HR projects filtered by technical skill category code (skCode).
    Maps to GET /api/hr-projects/skill-code/{skCode}."""
    if not skCode or not str(skCode).strip():
        return {"error": "Skill code cannot be empty"}

    return make_request(
        f"/api/hr-projects/skill-code/{quote(skCode)}"
    )

@tool
def fetchHrProjectsByClosedStatus(pClose: str) -> list:
    """Retrieves HR projects filtered by closure status ('y' for closed, 'n' for active/open).
    Maps to GET /api/hr-projects/closed/{pClose}."""
    if not pClose or not str(pClose).strip():
        return {"error": "Closed status cannot be empty"}

    return make_request(
        f"/api/hr-projects/closed/{quote(pClose)}"
    )

@tool
def fetchHrProjectsByEmployee(empNo: str) -> list:
    """Retrieves all HR projects assigned to or created by a specific employee.
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee' / 'hr_official_details'.
    Maps to GET /api/hr-projects/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/hr-projects/employee/{cleaned}")

@tool
def fetchHrProjectsByEmpNo(empNo: str) -> list:
    """Retrieves all HR projects assigned to or created by a specific employee using empNo [FOREIGN KEY].
    Maps to GET /api/hr-projects/employee/{empNo}."""
    return fetchHrProjectsByEmployee.func(empNo)
