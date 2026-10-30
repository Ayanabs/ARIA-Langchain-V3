from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllPositions() -> list:
    """Retrieves all position history records across the organisation from GET /api/positions.
    Database fields returned per record:
    - EmpNo (str/int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee'.
    - Promo_Dt (str): Date of promotion or position assignment (YYYY-MM-DD).
    - DivisionCode (int) [FOREIGN KEY]: Foreign key linking to 'divisioncode' in 'division' / 'hr_division_tbl'.
    - DesigCode (int) [FOREIGN KEY]: Foreign key linking to 'desigcode' in 'hr_designation_tbl'.
    - CategoryCode (int) [FOREIGN KEY]: Foreign key linking to 'categorycode' in 'category'.
    Maps to GET /api/positions."""
    return make_request("/api/positions")

@tool
def fetchPositionByEmpNo(empNo: str) -> dict:
    """Retrieves position history and promotion records for an employee by empNo.
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee number linking to 'empno' in 'employee'.
    Returns fields including Promo_Dt, DesignationCode [FK], DivisionCode [FK], CategoryCode [FK].
    Use when asked about an employee's position history, promotions, promotion date, or career advancement.
    Maps to GET /api/positions/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {
            "error": f"Invalid employee number format: {empNo}"
        }

    return make_request(
        f"/api/positions/{cleaned}"
    )

@tool
def fetchPositionsByDivisionCode(divisionCode: str) -> list:
    """Retrieves position history records for all employees in a specific division.
    Arguments & Foreign Key:
    - divisionCode (str/int) [FOREIGN KEY]: Numeric division code linking to 'divisioncode' in 'division' / 'hr_division_tbl'.
    Maps to GET /api/positions/division/{divisionCode}."""
    if not divisionCode or not str(divisionCode).strip():
        return {
            "error": "Division code cannot be empty"
        }

    return make_request(
        f"/api/positions/division/{str(divisionCode).strip()}"
    )

@tool
def fetchPositionsByDesigCode(desigCode: str) -> list:
    """Retrieves position history records for all employees holding a specific designation.
    Arguments & Foreign Key:
    - desigCode (str/int) [FOREIGN KEY]: Designation code linking to 'desigcode' in 'hr_designation_tbl'.
    Maps to GET /api/positions/designation/{desigCode}."""
    if not desigCode or not str(desigCode).strip():
        return {
            "error": "Designation code cannot be empty"
        }

    return make_request(
        f"/api/positions/designation/{str(desigCode).strip()}"
    )

@tool
def fetchPositionsByCategoryCode(categoryCode: str) -> list:
    """Retrieves position history records for all employees belonging to a specific category.
    Arguments & Foreign Key:
    - categoryCode (str/int) [FOREIGN KEY]: Category code linking to 'categorycode' in 'category'.
    Maps to GET /api/positions/category/{categoryCode}."""
    if not categoryCode or not str(categoryCode).strip():
        return {
            "error": "Category code cannot be empty"
        }

    return make_request(
        f"/api/positions/category/{str(categoryCode).strip()}"
    )

@tool
def fetchPositionsByPromoDate(promoDt: str) -> list:
    """Retrieves position and promotion records filtered by promotion date (Format: YYYY-MM-DD).
    Use when searching for employees promoted on a specific date or year.
    Maps to GET /api/positions/promotion-date/{promoDt}."""
    if not promoDt:
        return {
            "error": "Promotion date cannot be empty"
        }

    return make_request(
        f"/api/positions/promotion-date/{promoDt}"
    )

