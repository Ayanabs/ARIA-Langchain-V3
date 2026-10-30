from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id


@tool
def fetchAllHrOfficialDetails() -> list:
    """Retrieves official appointment and career details for all employees from GET /api/hr-official-details.
    Database fields returned per record:
    - empno (str/int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee'.
    - dateofappoinment (str): Date appointed to service (YYYY-MM-DD).
    - divisioncode (int) [FOREIGN KEY]: Foreign key linking to 'divisioncode' in 'division' / 'hr_division_tbl'.
    - desigcode (int) [FOREIGN KEY]: Foreign key linking to 'desigcode' in 'hr_designation_tbl'.
    - categorycode (int) [FOREIGN KEY]: Foreign key linking to 'categorycode' in 'category'.
    - salarycode (str) [FOREIGN KEY]: Foreign key linking to 'salarycode' in 'hr_salary_tbl'.
    - probationperiod (str): Date probation started or duration.
    - probationperiodto (str): Date probation ended / confirmation date.
    - retirementdt (str): Calculated mandatory retirement date.
    - incrementDate (str): Next annual salary increment date.
    - resignation (str): Date of resignation or retirement if applicable.
    - status (str): Active status code ('C' = Current/Active, 'RT' = Retired, 'RS' = Resigned).
    Maps to GET /api/hr-official-details."""
    return make_request("/api/hr-official-details")


@tool
def fetchHrOfficialDetailsByEmpNo(empNo: str) -> dict:
    """Retrieves official appointment and career record for a specific employee by empNo.
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee'.
    Returns fields including dateofappoinment, retirementdt, probationperiodto, incrementDate, divisioncode [FK], desigcode [FK], salarycode [FK].
    Use when asked about retirement date, years of service, appointment history, confirmation, or salary code for a specific employee.
    Maps to GET /api/hr-official-details/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    return make_request(f"/api/hr-official-details/{cleaned}")


@tool
def fetchHrOfficialDetailsByDivision(divisionCode: str) -> list:
    """Retrieves official career details for all employees in a specific division.
    Arguments & Foreign Key:
    - divisionCode (str/int) [FOREIGN KEY]: Numeric division code or division abbreviation (e.g. 'COM', 'IT', 'ITD', 5, 9) linking to 'divisioncode' in 'division'.
    Maps to GET /api/hr-official-details/division/{divisionCode} or GET /api/employees."""
    if not divisionCode or not str(divisionCode).strip():
        return {"error": "Division code cannot be empty"}

    from aria_agent.tools.division import resolve_division_code
    code_int = resolve_division_code(divisionCode)
    cleaned = str(code_int) if code_int is not None else clean_id(divisionCode)

    res = make_request(f"/api/hr-official-details/division/{cleaned}")
    if isinstance(res, list) and res:
        return res

    # Master employee fallback when division-specific endpoint experiences 500 error
    all_emp = make_request("/api/employees")
    if isinstance(all_emp, list) and all_emp:
        matched = [
            r for r in all_emp
            if isinstance(r, dict) and str(r.get("divisioncode") or r.get("divisionCode") or "") == str(cleaned)
        ]
        if matched:
            return matched

    return res if isinstance(res, list) else []


@tool
def fetchHrOfficialDetailsByDesignation(desigCode: str) -> list:
    """Retrieves official career details for all employees holding a specific designation.
    Arguments & Foreign Key:
    - desigCode (str/int) [FOREIGN KEY]: Designation code linking to 'desigcode' in 'hr_designation_tbl'.
    Maps to GET /api/hr-official-details/designation/{desigCode}."""
    if not desigCode or not str(desigCode).strip():
        return {"error": "Designation code cannot be empty"}

    return make_request(
        f"/api/hr-official-details/designation/{desigCode}"
    )


@tool
def fetchHrOfficialDetailsByCategory(category: str) -> list:
    """Retrieves official career details for all employees belonging to a specific staff category.
    Arguments & Foreign Key:
    - category (str/int) [FOREIGN KEY]: Category code linking to 'categorycode' in 'category'.
    Maps to GET /api/hr-official-details/category/{category}."""
    if not category or not str(category).strip():
        return {"error": "Category cannot be empty"}

    return make_request(
        f"/api/hr-official-details/category/{quote(category)}"
    )


@tool
def fetchHrOfficialDetailsByEmployeeStatus(empActive: str) -> list:
    """Retrieves official career records for ALL employees filtered by employment status code.
    Arguments:
    - empActive (str): Status code — 'C' = Current/Active, 'RT' = Retired, 'RS' = Resigned.
    Returns a bulk list of all employees with that status. Use ONLY for bulk/aggregate queries about a status group.
    Do NOT use this to look up a specific individual employee's official details —
    use the tool that accepts a single empNo parameter (individual employee lookup by ID) instead.
    Maps to GET /api/hr-official-details/active/{empActive}."""
    if not empActive or not str(empActive).strip():
        return {"error": "Employee status cannot be empty"}

    return make_request(
        f"/api/hr-official-details/active/{quote(empActive)}"
    )
