from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrDesigCadres() -> list:
    """Retrieves designation cadre allocation limits across divisions from GET /api/hr-desig-cadres.
    Database and JSON fields returned per record:
    - id (int): Primary key cadre record ID.
    - DesigCode (int) [FOREIGN KEY]: Foreign key linking to 'desigcode' in 'hr_designation_tbl'.
    - DivisionCode (int) [FOREIGN KEY]: Foreign key linking to 'divisioncode' in 'division' / 'hr_division_tbl'.
    - ApprovedCadre (int): Approved number of posts allocated for the designation in the division.
    Maps to GET /api/hr-desig-cadres."""
    return make_request("/api/hr-desig-cadres")
