import logging
from typing import Any, Optional, Tuple, Union
from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id
from aria_agent.config.config import is_admin_role, ADMIN_ROLES

_dep_logger = logging.getLogger(__name__)


def check_dependent_access_authorization(target_emp_no: Optional[str] = None) -> Optional[dict]:
    """Enforces authorization: Only administrators, HR managers, or the employee themselves
    can access family and dependent records.
    """
    from aria_agent.http.client import current_user_var
    user = current_user_var.get()
    if not user:
        return None  # Background task or test invocation without user context

    roles = [str(r).lower().strip() for r in getattr(user, "roles", [])]
    admin_check = is_admin_role(roles)
    hr_check = "hr_manager" in roles
    _dep_logger.info(
        "[DepAccess DIAG] user=%s | roles=%s | ADMIN_ROLES=%s | is_admin=%s | is_hr=%s | target_emp=%s",
        getattr(user, "username", "?"), roles, ADMIN_ROLES, admin_check, hr_check, target_emp_no
    )
    if admin_check or hr_check:
        return None  # Authorized for all records

    if target_emp_no is None:
        return {
            "error": "Access Denied: Organization-wide family and dependent records are restricted to administrators and HR managers."
        }

    from aria_agent.services.identity_resolver import resolve_universal_user_identity
    ident = resolve_universal_user_identity(user)
    caller_empno = str(ident.primary_id) if (ident and ident.primary_id) else None

    cleaned_target = str(clean_id(target_emp_no) or target_emp_no)
    if caller_empno and str(caller_empno) == cleaned_target:
        return None  # Authorized for own family records

    return {
        "error": f"Access Denied: Standard employees are only authorized to access their own family and dependent records. You cannot view family details for employee #{target_emp_no}."
    }


@tool
def fetchAllHrDepDetails() -> list:
    """Retrieves dependent family member records for all employees from GET /api/hr-dep-details.
    Database & JSON fields returned per record:
    - id (int): Auto-increment surrogate primary key (internal row ID, has no business meaning).
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    - relationship (int) [FOREIGN KEY]: Numeric relationship ID code (FK referencing primary key 'iD' in master table 'hr_dependent_relationship'). To decode what relationship each number represents (1=Husband, 2=Wife, 3=Son, 4=Daughter, 5=Father, 6=Mother, 7=Other), call 'fetchAllHrDependentRelationships'.
    - dependentName (str): Full name of dependent family member.
    - birthday (str): Dependent's Date of Birth (Format: YYYY-MM-DD).
    - idno (str): Dependent's National Identity Card (NIC) or Identity Document number.
    Restricted: Administrators and HR managers only.
    Maps to GET /api/hr-dep-details."""
    auth_err = check_dependent_access_authorization(None)
    if auth_err:
        return [auth_err]
    return make_request("/api/hr-dep-details")


@tool
def fetchHrDepDetailsByEmployee(empNo: Union[str, int]) -> list:
    """Retrieves dependent family member records for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Database & JSON fields returned per record:
    - id (int): Auto-increment surrogate primary key (internal row ID, has no business meaning and is NOT an employee number or relationship code).
    - empNo (int) [FOREIGN KEY]: Employee Number.
    - relationship (int) [FOREIGN KEY]: Numeric relationship ID code (e.g. 1, 2, 3, 4, etc.). This is a FOREIGN KEY referencing the primary key 'iD' in the master lookup table 'hr_dependent_relationship'. It does NOT contain text names directly.
    - dependentName (str): Full name of the dependent family member.
    - birthday (str): Dependent's Date of Birth (Format: YYYY-MM-DD).
    - idno (str): Dependent's National Identity Card (NIC) or Identity Document number.
    SCHEMA RELATION: Because 'relationship' is an integer foreign key (e.g. 1, 3, 4), call 'fetchAllHrDependentRelationships' from 'hr_dependent_relationship' to decode and present the exact human-readable family relationship titles (1=Husband, 2=Wife, 3=Son, 4=Daughter, 5=Father, 6=Mother, 7=Other).
    Use when asked about an employee's family, family members, relations, relatives, relationship, spouse, husband, wife, children, kids, son, daughter, father, mother, or dependents.
    Note: Standard employees are authorized to access their own family records only; administrators and HR managers have organization-wide access.
    Maps to GET /api/hr-dep-details/employee/{empNo}."""
    cleaned = clean_id(empNo)
    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    auth_err = check_dependent_access_authorization(cleaned)
    if auth_err:
        return [auth_err]

    return make_request(f"/api/hr-dep-details/employee/{cleaned}")


@tool
def fetchHrDepDetailsByRelationship(relationship: str) -> list:
    """Retrieves employee dependent records filtered by numeric family relationship ID.
    Arguments:
    - relationship (str/int) [FOREIGN KEY]: Numeric relationship ID code referencing 'iD' in 'hr_dependent_relationship' (e.g. 1 for Husband, 2 for Wife, 3 for Son, 4 for Daughter, 5 for Father, 6 for Mother, 7 for Other). Use 'fetchAllHrDependentRelationships' or 'searchHrDependentRelationshipsByName' to get the numeric ID first if searching by name.
    Returns fields:
    - id (int): Auto-increment surrogate primary key (internal row ID).
    - empNo (int) [FOREIGN KEY]: Employee Number.
    - relationship (int) [FOREIGN KEY]: Numeric relationship ID code.
    - dependentName (str): Full name of dependent.
    - birthday (str): Date of birth (YYYY-MM-DD).
    - idno (str): NIC number.
    Restricted: Administrators and HR managers only.
    Maps to GET /api/hr-dep-details/relationship/{relationship}."""
    auth_err = check_dependent_access_authorization(None)
    if auth_err:
        return [auth_err]

    cleaned = clean_id(relationship)
    if not cleaned:
        return {"error": f"Invalid relationship ID format: {relationship}"}

    return make_request(f"/api/hr-dep-details/relationship/{cleaned}")


@tool
def searchHrDepDetailsByName(name: str) -> list:
    """Searches employee dependent records by full or partial dependent name.
    Returns fields:
    - id (int): Auto-increment surrogate primary key (internal row ID).
    - empNo (int) [FOREIGN KEY]: Employee Number linking to 'employee'.
    - relationship (int) [FOREIGN KEY]: Numeric relationship ID code referencing 'iD' in 'hr_dependent_relationship' (1=Husband, 2=Wife, 3=Son, 4=Daughter, 5=Father, 6=Mother, 7=Other).
    - dependentName (str): Full name of dependent family member.
    - birthday (str): Date of birth.
    - idno (str): NIC number.
    Restricted: Administrators and HR managers only.
    Maps to GET /api/hr-dep-details/search?name={name}."""
    auth_err = check_dependent_access_authorization(None)
    if auth_err:
        return [auth_err]

    if not name or not str(name).strip():
        return {"error": "Name cannot be empty"}

    return make_request(f"/api/hr-dep-details/search?name={quote(name)}")


@tool
def fetchHrDepDetailsByEmpNo(empNo: Union[str, int]) -> Any:
    """Retrieves dependent family member records for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Database & JSON fields returned per record:
    - id (int): Auto-increment surrogate primary key (internal row ID, has no business meaning and is NOT an employee number or relationship code).
    - empNo (int) [FOREIGN KEY]: Employee Number.
    - relationship (int) [FOREIGN KEY]: Numeric relationship ID code (e.g. 1, 2, 3, 4, etc.). This is a FOREIGN KEY referencing the primary key 'iD' in master lookup table 'hr_dependent_relationship' (1=Husband, 2=Wife, 3=Son, 4=Daughter, 5=Father, 6=Mother, 7=Other).
    - dependentName (str): Full name of the dependent family member.
    - birthday (str): Dependent's Date of Birth (Format: YYYY-MM-DD).
    - idno (str): Dependent's National Identity Card (NIC) or Identity Document number.
    SCHEMA RELATION: Because 'relationship' is an integer foreign key (e.g. 1, 3, 4), call 'fetchAllHrDependentRelationships' from 'hr_dependent_relationship' to decode and present the exact human-readable family relationship titles (1=Husband, 2=Wife, 3=Son, 4=Daughter, 5=Father, 6=Mother, 7=Other).
    Use when asked about an employee's family, family members, relations, relatives, relationship, spouse, husband, wife, children, kids, son, daughter, father, mother, or dependents.
    Note: Standard employees are authorized to access their own family records only; administrators and HR managers have organization-wide access.
    Maps to GET /api/hr-dep-details/employee/{empNo}."""
    return fetchHrDepDetailsByEmployee.func(empNo)
