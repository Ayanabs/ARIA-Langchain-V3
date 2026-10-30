from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllCategories() -> list:
    """Retrieves all staff work category and shift schedule records from GET /api/categories.
    Database & JSON fields returned per record:
    - CategoryCode (int) [PRIMARY KEY / FOREIGN KEY]: Staff category code. Referenced by 'categorycode' in 'employee', 'hr_official_details', 'positions_tbl'.
    - Category (str): Staff category description or group name.
    - InTime (str): Scheduled work start/in time.
    - OutTimeH, OutTimeM (str/int): Scheduled work end/out time (hours and minutes).
    - LateTime / SP_LateTime (str/int): Late arrival grace time threshold.
    Maps to GET /api/categories."""
    return make_request("/api/categories")

@tool
def fetchCategoryByCategory(category: str) -> dict:
    """Retrieves staff work category schedule details by category description or group name.
    Returns fields including CategoryCode [PK/FK], Category, InTime, OutTimeH, OutTimeM, LateTime.
    Maps to GET /api/categories/category/{category}."""
    if not category or not str(category).strip():
        return {"error": "Category name cannot be empty"}
    return make_request(f"/api/categories/category/{category}")

@tool
def fetchCategoryByCode(categoryCode: int) -> dict:
    """Retrieves work category shift & time rules by numeric category code (CategoryCode).
    Arguments & Foreign Key:
    - categoryCode (int) [FOREIGN KEY]: Staff category code linking to 'categorycode' in 'employee', 'hr_official_details', 'positions_tbl'.
    Returns fields: CategoryCode [PK/FK], Category, InTime (start/entry time), OutTimeH/OutTimeM (end/leaving time), LateTime.
    Maps to GET /api/categories/{categoryCode}."""
    cleaned = clean_id(categoryCode)
    if not cleaned:
        return {"error": "Invalid categoryCode"}
    res = make_request(f"/api/categories/{cleaned}")
    if isinstance(res, dict) and "error" not in res and res:
        return res
    fallback = make_request(f"/api/categories/code/{cleaned}")
    return res if (isinstance(res, dict) and "error" not in res) else fallback

@tool
def fetchCategoryLeavingAndEntryTimes(category: str = "", categoryCode: int = None) -> dict:
    """Retrieves the scheduled entry time and leaving time for a staff work category.
    Arguments:
    - category (str, optional): Work category description or name (e.g. 'Engineering', 'Administrative').
    - categoryCode (int, optional): Numeric category code.
    Returns:
    - category (str): Category description.
    - entry_time (str): Scheduled morning entry / in-time (Format: HH:MM:SS, e.g. '08:30:00').
    - leaving_time (str): Scheduled departure / leaving time (Format: HH:MM, e.g. '16:15').
    - late_threshold (str): Grace limit before marked as late.
    - adjustment_time (str): Shift adjustment time.
    Use when asked about work category working hours, entry times, or leaving times.
    Maps to GET /api/categories/category/{category} or GET /api/categories/{categoryCode}."""
    cat_data = None
    if categoryCode is not None:
        cat_data = fetchCategoryByCode.func(categoryCode)
    elif category and str(category).strip():
        cat_data = fetchCategoryByCategory.func(str(category).strip())
    else:
        return {"error": "Must provide either category name or categoryCode"}

    if not isinstance(cat_data, dict) or "error" in cat_data:
        return cat_data or {"error": "Category schedule not found"}

    out_h = cat_data.get("outtimeh")
    out_m = cat_data.get("outtimem", 0)
    leaving_time = None
    if out_h is not None:
        try:
            leaving_time = f"{int(out_h):02d}:{int(out_m or 0):02d}"
        except (ValueError, TypeError):
            leaving_time = f"{out_h}:{out_m}"

    return {
        "categoryCode": cat_data.get("categorycode"),
        "category": cat_data.get("category"),
        "entry_time": cat_data.get("intime"),
        "leaving_time": leaving_time,
        "late_threshold": cat_data.get("latetime"),
        "adjustment_time": cat_data.get("adjesttime"),
        "special_late_time": cat_data.get("spLatetime")
    }

