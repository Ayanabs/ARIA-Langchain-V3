from langchain_core.tools import tool
from aria_agent.schemas.retrieval import ReadLimit
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrIncrementReports() -> list:
    """Retrieves annual salary increment report records for all employees from GET /api/hr-increment-reports.
    Database & JSON fields returned per record:
    - id (int): Primary key increment report ID.
    - name (str): Full name of employee.
    - designation (str) [FOREIGN KEY]: Designation title (linking to 'hr_designation_tbl').
    - salary_scale (str) [FOREIGN KEY]: Salary scale code/specification (linking to 'hr_salary_tbl').
    - present_salary_point (float): Current monthly basic salary point in the configured currency before increment.
    - inc_date (str): Scheduled salary increment date (Format: YYYY-MM-DD).
    - inc_value (float): Annual increment step monetary value in the configured currency.
    - basic_salary (float): Updated basic salary amount after increment.
    - rec_punsh / pass_exam (str): Disciplinary records or exam pass status for increment eligibility.
    Maps to GET /api/hr-increment-reports."""
    return make_request("/api/hr-increment-reports")

@tool
def fetchHrIncrementReportsByDesignation(designation: str) -> list:
    """Retrieves annual salary increment reports filtered by Designation title.
    Arguments & Foreign Key:
    - designation (str) [FOREIGN KEY]: Designation job title linking to 'hr_designation_tbl'.
    Returns fields: name, designation [FK], salary_scale [FK], present_salary_point, inc_date (increment date), inc_value (increment amount), basic_salary.
    Maps to GET /api/hr-increment-reports/designation/{designation}."""
    if not designation or not str(designation).strip():
        return {"error": "Designation cannot be empty"}

    return make_request(
        f"/api/hr-increment-reports/designation/{designation}"
    )

@tool
def fetchHrIncrementReportsByIncrementDate(incDate: str) -> list:
    """Retrieves salary increment reports filtered by scheduled increment date (incDate, Format: YYYY-MM-DD).
    Maps to GET /api/hr-increment-reports/increment-date/{incDate}."""
    if not incDate or not str(incDate).strip():
        return {"error": "Increment date cannot be empty"}

    return make_request(
        f"/api/hr-increment-reports/increment-date/{incDate}"
    )

@tool
def fetchHrIncrementReportsByIncrementValue(incValue: str) -> list:
    """Retrieves salary increment reports filtered by annual increment monetary step value (incValue in the configured currency).
    Maps to GET /api/hr-increment-reports/increment-value/{incValue}."""
    cleaned = clean_id(incValue)

    if not cleaned:
        return {"error": f"Invalid increment value format: {incValue}"}

    return make_request(
        f"/api/hr-increment-reports/increment-value/{cleaned}"
    )


@tool
def fetchHrIncrementReportsByDateRange(
    startDate: str,
    endDate: str,
    fullname: str = "",
    designation: str = "",
    limit: ReadLimit = 250
) -> list:
    """Retrieves employee salary increments, annual increment reports, and increment step values whose scheduled dates fall within the calendar date range [startDate, endDate].

    DYNAMIC DATE RANGE GENERATION (startDate and endDate variables):
    - When the user asks for salary increments across a time window (e.g. "salary increments in the last 3 years", "increments in the last 2 years", "increments scheduled between X and Y", "increments of Rasika in the last 3 years"):
      * You (the LLM) must dynamically compute and set BOTH date variables ('startDate' and 'endDate') in YYYY-MM-DD format based on the prompt.

    ARGUMENTS:
    - startDate (str): Beginning of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - endDate (str): End of date range inclusive (Format: YYYY-MM-DD). You must calculate and set this string.
    - fullname (str, optional): Employee full or partial name.
    - designation (str, optional): Designation title filter.
    - limit (int, optional): Max records to return (default 250).

    RETURNS:
    List of increment records with fields: name, designation, salaryScale, presentSalaryPoint, incDate, incValue, basicSalary.
    Maps to /api/hr-increment-reports.
    """
    s_dt = str(startDate).strip() if startDate else ""
    e_dt = str(endDate).strip() if endDate else ""
    if not s_dt or not e_dt:
        return [{"error": "Both startDate and endDate (YYYY-MM-DD) are required"}]

    increments = make_request("/api/hr-increment-reports")
    if not isinstance(increments, list):
        return []

    filtered = []
    clean_name = str(fullname).strip().lower() if fullname else ""
    clean_desig = str(designation).strip().lower() if designation else ""

    for inc in increments:
        if not isinstance(inc, dict):
            continue
        inc_d = str(inc.get("incDate") or inc.get("inc_date") or "").strip()
        if not (s_dt <= inc_d <= e_dt):
            continue
        if clean_name and clean_name not in str(inc.get("name") or "").lower():
            continue
        if clean_desig and clean_desig not in str(inc.get("designation") or "").lower():
            continue
        filtered.append(inc)

    sorted_incs = sorted(filtered, key=lambda x: str(x.get("incDate", "")), reverse=True)
    return sorted_incs[:limit] if limit else sorted_incs

