from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllDivBudgets() -> list:
    """Retrieves all division budget records across the organisation from GET /api/div-budgets.
    Database fields returned per record:
    - divb_code (int): Primary key budget allocation ID.
    - div_code (int) [FOREIGN KEY]: Foreign key linking to 'divisioncode' in 'division' / 'hr_division_tbl'. Identifies the division.
    - budg_code (str): Accounting budget line item code.
    - budg_year (str): Financial budget year (e.g. '2024').
    - user_descrip (str): Description or purpose of allocation.
    - req_amount (float): Requested budget amount.
    - appr_amount (float): Approved budget amount.
    - the_amount (float): Final actual allocated amount.
    Maps to GET /api/div-budgets."""
    return make_request("/api/div-budgets")

@tool
def fetchDivBudgetsByDivisionCode(divCode: str) -> list:
    """Retrieves annual budget allocations for a specific division using divCode.
    Arguments & Foreign Key:
    - divCode (str/int) [FOREIGN KEY]: Numeric division code linking to 'divisioncode' in 'division' / 'hr_division_tbl'.
    Maps to GET /api/div-budgets/division/{divCode}."""
    if not divCode or not str(divCode).strip():
        return {"error": "Division code cannot be empty"}

    return make_request(f"/api/div-budgets/division/{divCode}")

@tool
def fetchDivBudgetsByBudgetYear(budgYear: str) -> list:
    """Retrieves division budget allocations for a specific financial budget year (e.g. '2024', '2025').
    Returns fields including div_code [FK], budg_code, req_amount, appr_amount, the_amount.
    Maps to GET /api/div-budgets/year/{budgYear}."""
    if not budgYear or not str(budgYear).strip():
        return {"error": "Budget year cannot be empty"}

    return make_request(f"/api/div-budgets/year/{budgYear}")


@tool
def fetchDivBudgetsByYearRange(
    startYear: int,
    endYear: int,
    divCode: str = ""
) -> list:
    """Retrieves division annual budget allocations across a multi-year range [startYear, endYear].

    DYNAMIC YEAR RANGE GENERATION (startYear and endYear variables):
    - When the user asks for division budgets over a time range (e.g. "budgets between 2020 and 2024", "budgets in the last 3 years", "past 5 years of budgets"):
      * You (the LLM) must dynamically compute and set BOTH integer year variables ('startYear' and 'endYear'):
        1. Explicit Years: For "budgets between 2020 and 2024", set startYear=2020, endYear=2024.
        2. Relative Years: For "budgets in the last 3 years" relative to 2024, set startYear=2021, endYear=2024.

    ARGUMENTS:
    - startYear (int): Starting financial year (e.g. 2020).
    - endYear (int): Ending financial year (e.g. 2024).
    - divCode (str/int, optional): Numeric division code (e.g. 9) OR division name/acronym (e.g. 'IT', 'ITD'). Automatically resolved.

    RETURNS:
    List of division budget allocations with fields: budgCode, budgYear, divCode, reqAmount, apprAmount, theAmount, userDescrip.
    Maps to /api/div-budgets.
    """
    try:
        s_yr = int(startYear)
        e_yr = int(endYear)
    except (ValueError, TypeError):
        return [{"error": "Both startYear and endYear must be valid integers (e.g. 2021, 2024)"}]

    if s_yr > e_yr:
        s_yr, e_yr = e_yr, s_yr

    target_div = None
    if divCode and str(divCode).strip():
        from aria_agent.tools.division import resolve_division_code
        target_div = resolve_division_code(divCode) or clean_id(divCode)

    if target_div is not None:
        budgets = make_request(f"/api/div-budgets/division/{target_div}")
    else:
        budgets = make_request("/api/div-budgets")

    if not isinstance(budgets, list):
        return []

    filtered = []
    for b in budgets:
        if not isinstance(b, dict):
            continue
        raw_yr = str(b.get("budgYear") or "").strip()
        yr_val = None
        if len(raw_yr) >= 4 and raw_yr[:4].isdigit():
            yr_val = int(raw_yr[:4])
        if yr_val is not None and s_yr <= yr_val <= e_yr:
            filtered.append(b)

    return sorted(filtered, key=lambda x: str(x.get("budgYear", "")), reverse=True)

