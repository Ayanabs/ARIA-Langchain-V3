from langchain_core.tools import tool
from aria_agent.schemas.retrieval import ReadLimit
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPrProjects() -> list:
    """Retrieves all PR project records across the organisation from GET /api/pr-projects.
    WARNING: Do NOT use this tool when querying projects of a specific division, department, or unit. Use fetchPrProjectsByDivision instead.
    Database fields returned per record:
    - serial_no (int): Primary key row sequence number.
    - code (str): Unique PR project code (e.g. 'PR/2023/EE/001').
    - pname (str): Full project title/name.
    - div_code / divCode (int) [FOREIGN KEY]: Foreign key linking to 'divisioncode' in 'division' / 'hr_division_tbl'. Identifies managing division.
    - pt_code / ptCode (int) [FOREIGN KEY]: Foreign key linking to 'pt_code' in 'pr_project_types'. Identifies project type.
    - ptype (str): Project classification name.
    - cname (str): Client or sponsoring organization name.
    - apcode (str): Approval/accounting tracking code.
    - sk_code (str): Technical skill category code.
    - startdate (str): Project start date (YYYY-MM-DD).
    - enddate (str): Target completion date (YYYY-MM-DD).
    - confirm (str): Confirmation status ('y' = confirmed, 'n' = pending).
    - p_close (str): Closure status ('y' = closed, 'n' = active).
    - year (int): Year of project initiation.
    Maps to GET /api/pr-projects."""
    return make_request("/api/pr-projects")

@tool
def fetchPrProjectBySerialNo(serialNo: int) -> dict:
    """Retrieves a single PR project record by primary key serial sequence number (serialNo [PK]).
    Maps to GET /api/pr-projects/{serialNo}."""
    return make_request(f"/api/pr-projects/{serialNo}")


@tool
def fetchPrProjectsByYear(year: str) -> list:
    """Retrieves PR projects filtered by initiation year (e.g. '2023', '2024').
    Returns project fields including div_code [FK], pt_code [FK], code, pname, cname.
    Maps to GET /api/pr-projects/year/{year}."""

    cleaned = clean_id(year)
    if not cleaned:
        return {"error": f"Invalid year format: {year}"}
    return make_request(f"/api/pr-projects/year/{cleaned}")

@tool
def fetchPrProjectsByDivision(divCode: str = "", divisionCode: str = "", division: str = "") -> list:
    """Retrieves all institutional, software, engineering, and research projects (PR projects) managed by or belonging to an internal technical division of the organization (e.g. IT Division, Electronics Division, Communications Division).
    WARNING: Do NOT use this tool for external client organizations, sponsors, funders, ministries, or external departments. For external clients, sponsors, or partner organizations, use fetchPrProjectsByClient instead.
    Arguments:
    - divCode (str/int): Numeric division code (e.g. 9) OR division name / abbreviation (e.g. 'IT', 'ITD', 'COM'). Automatically resolves internal division names and acronyms.
    Maps to GET /api/pr-projects/division/{divCode}."""
    target_code = divCode or divisionCode or division or ""
    target_str = str(target_code).strip()
    if target_str.isdigit() and len(target_str) == 4 and 1900 <= int(target_str) <= 2100:
        return {"error": f"'{target_str}' is a calendar year, not a division. Use fetchPrProjectsByYear(year='{target_str}') instead."}
    from aria_agent.tools.division import resolve_division_code
    code_int = resolve_division_code(target_code)
    if code_int is not None:
        return make_request(f"/api/pr-projects/division/{code_int}")
    cleaned = clean_id(target_code)
    if not cleaned:
        return {"error": f"Invalid division code or name: {target_code}"}
    return make_request(f"/api/pr-projects/division/{cleaned}")

@tool
def fetchPrProjectsByProjectType(ptCode: str) -> list:
    """Retrieves PR projects filtered strictly by numeric project classification type code (ptCode linking to 'pt_code' in 'pr_project_types', e.g. 1, 2, 3).
    WARNING: Do NOT use this tool for department or division queries (use fetchPrProjectsByDivision instead).
    Maps to GET /api/pr-projects/project-type/{ptCode}."""
    cleaned = clean_id(ptCode)
    if not cleaned:
        return {"error": f"Invalid project type code format: {ptCode}"}
    return make_request(f"/api/pr-projects/project-type/{cleaned}")

@tool
def fetchPrProjectsByCode(code: str) -> list:
    """Retrieves PR project details matching a specific unique project code (e.g. 'PR/2023/EE/001').
    Returns fields including div_code [FK], pt_code [FK], pname, cname, startdate, enddate.
    Maps to GET /api/pr-projects/code/{code}."""
    if not code or not str(code).strip():
        return {"error": "Project code cannot be empty"}
    return make_request(f"/api/pr-projects/code/{quote(code)}")

@tool
def fetchPrProjectsByProjectName(pname: str) -> list:
    """Retrieves PR projects matching a full or partial project title/name.
    Maps to GET /api/pr-projects/name/{pname}."""
    if not pname or not str(pname).strip():
        return {"error": "Project name cannot be empty"}
    return make_request(f"/api/pr-projects/name/{quote(pname)}")

@tool
def fetchPrProjectsByApCode(apcode: str) -> list:
    """Retrieves PR projects filtered by approval/accounting code (apcode).
    Maps to GET /api/pr-projects/apcode/{apcode}."""
    if not apcode or not str(apcode).strip():
        return {"error": "AP code cannot be empty"}
    return make_request(f"/api/pr-projects/apcode/{quote(apcode)}")

@tool
def fetchPrProjectsByPType(ptype: str) -> list:
    """Retrieves PR projects filtered strictly by project classification type description/name (ptype, e.g. 'Client based', 'Inhouse', 'Consultancy').
    WARNING: Do NOT use this tool for department or division queries (e.g. do not pass 'IT', 'Information Technology', or division names here; use fetchPrProjectsByDivision instead).
    Maps to GET /api/pr-projects/ptype/{ptype}."""
    if not ptype or not str(ptype).strip():
        return {"error": "Project type cannot be empty"}
    return make_request(f"/api/pr-projects/ptype/{quote(ptype)}")

@tool
def fetchPrProjectsByClient(cname: str) -> list:
    """Retrieves institutional, software, engineering, and research PR projects funded by, sponsored by, or executed for an external client, sponsor, customer, or partner organization.
    Use this tool whenever the user asks for projects related to, funded by, or sponsored by an external client, sponsor, partner institution, ministry, or government department.
    Searches against client/sponsor name (cname). Supports full or partial organization names.
    Maps to GET /api/pr-projects/client/{cname}."""
    if not cname or not str(cname).strip():
        return {"error": "Client name cannot be empty"}
    return make_request(f"/api/pr-projects/client/{quote(cname)}")

@tool
def fetchPrProjectsByStatus(confirm: str) -> list:
    """Retrieves PR projects filtered by confirmation status ('y' for confirmed, 'n' for pending).
    Maps to GET /api/pr-projects/status/{confirm}."""
    if not confirm or not str(confirm).strip():
        return {"error": "Status cannot be empty"}
    return make_request(f"/api/pr-projects/status/{quote(confirm)}")

@tool
def fetchPrProjectsBySkillCode(skCode: str) -> list:
    """Retrieves PR projects filtered by technical skill category code (skCode).
    Maps to GET /api/pr-projects/skill-code/{skCode}."""
    if not skCode or not str(skCode).strip():
        return {"error": "Skill code cannot be empty"}
    return make_request(f"/api/pr-projects/skill-code/{quote(skCode)}")

@tool
def fetchPrProjectsByClosedStatus(pClose: str) -> list:
    """Retrieves PR projects filtered by closure status ('y' for closed, 'n' for active).
    Maps to GET /api/pr-projects/closed/{pClose}."""
    if not pClose or not str(pClose).strip():
        return {"error": "Closed status cannot be empty"}
    return make_request(f"/api/pr-projects/closed/{quote(pClose)}")

@tool
def fetchPrProjectsByEmployee(empNo: str) -> list:
    """Retrieves all PR projects created by, assigned to, or closed by a specific employee (matching 'user' or 'p_close_user' column mapped to empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee'.
    Maps to GET /api/pr-projects/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}
    return make_request(f"/api/pr-projects/employee/{cleaned}")


@tool
def fetchPrProjectsByEmpNo(empNo: str) -> list:
    """Retrieves all PR projects assigned to or created by a specific employee using empNo [FOREIGN KEY].
    Maps to GET /api/pr-projects/employee/{empNo}."""
    return fetchPrProjectsByEmployee.func(empNo)


@tool
def fetchPrProjectsByDateRange(
    startDate: str,
    endDate: str,
    divCode: str = "",
    limit: ReadLimit = 250
) -> list:
    """Retrieves research, engineering, and consultancy projects (PR projects) whose start dates or active lifespans fall within the date range [startDate, endDate].

    DYNAMIC DATE RANGE GENERATION (startDate and endDate variables):
    - When the user asks for projects across a relative time window (e.g. "projects in the last 3 years", "projects started in the past 12 months", "recent projects", "projects from 2021 to 2023"):
      * You (the LLM) must dynamically compute and set BOTH date variables ('startDate' and 'endDate') in YYYY-MM-DD format based on the prompt:
        1. Explicit Dates: For "between 2021-01-01 and 2023-12-31", set startDate='2021-01-01', endDate='2023-12-31'.
        2. Relative Years/Months: For "projects in the last 3 years", subtract 3 years from today's reference date (e.g. startDate='2023-01-01', endDate='2026-09-24').
        3. Year Ranges: For "projects from 2021 to 2023", set startDate='2021-01-01' and endDate='2023-12-31'.

    ARGUMENTS:
    - startDate (str): Beginning of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - endDate (str): End of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - divCode (str/int, optional): Numeric division code (e.g. 9) OR division acronym/name (e.g. 'IT', 'ITD', 'COM'). Automatically resolved.
    - limit (int, optional): Max projects to return (default 250).

    RETURNS:
    List of project records with fields: code, pname, startdate, enddate, year, divCode, ptype, cname, capital, recurrent, status.
    Maps to /api/pr-projects.
    """
    s_dt = str(startDate).strip() if startDate else ""
    e_dt = str(endDate).strip() if endDate else ""
    if not s_dt or not e_dt:
        return [{"error": "Both startDate and endDate (YYYY-MM-DD) are required"}]

    target_div = None
    if divCode and str(divCode).strip():
        from aria_agent.tools.division import resolve_division_code
        target_div = resolve_division_code(divCode) or clean_id(divCode)

    if target_div is not None:
        projects = make_request(f"/api/pr-projects/division/{target_div}")
    else:
        projects = make_request("/api/pr-projects")

    if not isinstance(projects, list):
        return []

    filtered = [
        p for p in projects
        if isinstance(p, dict) and p.get("startdate") and s_dt <= str(p.get("startdate")) <= e_dt
    ]
    if not filtered:
        # Check active window
        filtered = [
            p for p in projects
            if isinstance(p, dict) and p.get("startdate") and str(p.get("startdate")) <= e_dt
            and (not p.get("enddate") or str(p.get("enddate")) >= s_dt)
        ]

    sorted_projects = sorted(filtered, key=lambda x: (str(x.get("year", "")), str(x.get("startdate", ""))), reverse=True)
    return sorted_projects[:limit] if limit else sorted_projects



