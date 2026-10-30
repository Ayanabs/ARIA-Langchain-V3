import time
from typing import Any, Dict
from urllib.parse import quote
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

_NAMES_CACHE: Dict[str, str] = {}
_NAMES_CACHE_TIME: float = 0.0
_ALL_EMPLOYEES_CACHE: Any = None
_ALL_EMPLOYEES_CACHE_TIME: float = 0.0

def _get_names_map() -> Dict[str, str]:
    from aria_agent.services.request_read_cache import cached_read
    try:
        names_data = cached_read("/api/employees/names", lambda: make_request("/api/employees/names", is_chat_metadata=True))
        if isinstance(names_data, list):
            return {
                str(clean_id(r.get("empno"))): str(r.get("fullname") or "")
                for r in names_data
                if isinstance(r, dict) and r.get("empno")
            }
    except Exception:
        pass
    return {}

def _get_all_employees_cached() -> list:
    from aria_agent.services.request_read_cache import cached_read
    try:
        res = cached_read("/api/employees", lambda: make_request("/api/employees"))
        if isinstance(res, list) and res:
            return res
    except Exception:
        pass
    return []

@tool
def fetchAllEmployees() -> list:
    """Retrieves the authoritative complete master list of all employees in the organisation from GET /api/employees.
    Database & JSON fields returned per record:
    - empno (str/int) [PRIMARY KEY / FOREIGN KEY]: Employee Number (unique staff identifier).
    - fullname / empNamewithInit (str): Employee Full Name.
    - email (str): Official work email address.
    - designation (str) / desigcode (int) [FOREIGN KEY]: Designation job title and designation code (linking to 'hr_designation_tbl').
    - divisioncode (int) [FOREIGN KEY]: Numeric division code (linking to 'division' / 'hr_division_tbl').
    - salarycode (str) [FOREIGN KEY]: Salary scale code (linking to 'hr_salary_tbl').
    - grade (str): Salary grade (e.g. 'I', 'II', 'III').
    - status (str): Active employment status ('Active', 'Retired', 'Resigned').
    - nic / nicnum (str): National Identity Card (NIC) Number.
    - dateOfBirth / dob (str): Date of Birth (DOB, Format: YYYY-MM-DD).
    - appointmentDate (str): Date appointed to service (Format: YYYY-MM-DD).
    - mobile (str): Mobile phone contact number.
    - address (str): Residential address.
    - maritalStatus (str): Marital status ('Single', 'Married').
    - gender (str): Gender ('Male', 'Female').
    - title (str): Salutation title ('Mr', 'Miss', 'Mrs', 'Dr', 'Prof', 'Eng').
    - categorycode (int) [FOREIGN KEY]: Staff category code (linking to 'category').
    - emptypecode (str) [FOREIGN KEY]: Employment type code.
    Use as the primary tool when asked about all employees, organization-wide staff directory, employee birthdays, staff born in this month or next month, age demographics, or retirements.
    Maps to GET /api/employees."""
    return make_request("/api/employees")

@tool
def fetchAllEmployeeNames() -> list:
    """Retrieves lightweight name and ID records for all employees.
    Fields returned: empno (Employee Number), fullname (Full Name), empNamewithInit (Name with Initials).
    Maps to GET /api/employees/names."""
    return make_request("/api/employees/names")

@tool
def fetchEmployeeByEmail(email: str) -> dict:
    """Retrieves the full employee record matching a specific work email address.
    Use for self-referential queries ("my details", "who am I", "my salary", "my retirement date", "my service years").
    Returns fields including: empno [PK/FK], fullname, email, dateOfBirth (DOB), appointmentDate (service start date), nic (NIC number), divisioncode [FK], desigcode [FK].
    Maps to GET /api/employees/email/{email}."""
    if not email or not str(email).strip():
        return {"error": "Email cannot be empty"}

    return make_request(f"/api/employees/email/{email}")

@tool
def fetchEmployeeByEmpno(empno: str) -> Any:
    """Retrieves the full employee record by Employee Number (empno).
    Arguments & Primary/Foreign Key:
    - empno (str/int) [PRIMARY KEY / FOREIGN KEY]: Employee Number (unique staff identifier).
    Returns fields including fullname, email, nic (NIC number), dateOfBirth (DOB), appointmentDate (appointment start date), divisioncode [FK], desigcode [FK], salarycode [FK].
    Maps to GET /api/employees/empno/{empno}."""
    cleaned = str(empno).strip() if empno is not None else ""
    if not cleaned:
        return {"error": "Employee number (empno) cannot be empty"}
    # If a textual person/entity name is passed instead of a numeric employee number, gracefully delegate to fullname lookup
    if not cleaned.isdigit() and any(c.isalpha() for c in cleaned):
        return make_request(f"/api/employees/fullname/{cleaned}")
    return make_request(f"/api/employees/empno/{cleaned}")

@tool
def fetchEmployeeByNicnum(nicnum: str) -> dict:
    """Retrieves an employee record by National Identity Card (NIC) number.
    Arguments:
    - nicnum (str): National Identity Card number (e.g. '199512345678' or '951234567V').
    Returns fields including empno [FK], fullname, email, dateOfBirth (DOB), appointmentDate, divisioncode [FK].
    Maps to GET /api/employees/nic/{nicnum}."""
    if not nicnum or not str(nicnum).strip():
        return {"error": "NIC number cannot be empty"}

    return make_request(f"/api/employees/nic/{nicnum}")

@tool
def fetchEmployeesByPhone(phone: str) -> list:
    """Retrieves employee records matching a telephone or mobile phone number.
    Maps to GET /api/employees/phone/{phone}."""
    return make_request(f"/api/employees/phone/{phone}")

@tool
def fetchEmployeesByFullname(fullname: str) -> list:
    """Searches for employees by full name (case-insensitive partial match).
    Primary tool when a person's name is mentioned in the prompt, or when searching for employee contact info, mobile number, phone, address, NIC number (nicnum), email, designation, or division.
    Returns complete employee master records containing: empno (Employee Number), fullname, email, mobileno (mobile phone number), phoneResidence, address, nicnum (NIC number), dateOfBirth (DOB), appointmentDate, designation, divisioncode, salarycode.
    Always extract and use the 'empno' from this result for subsequent employee detail tool calls.
    Maps to GET /api/employees/fullname/{fullname}."""
    return make_request(f"/api/employees/fullname/{fullname}")

@tool
def fetchEmployeesByName(name: str) -> list:
    """Searches for employees by name or full name (case-insensitive partial match).
    Primary tool when a person's name is mentioned in the prompt, or when searching for employee contact info, mobile number, phone, address, NIC number (nicnum), email, designation, or division.
    Returns complete employee master records containing: empno (Employee Number), fullname, email, mobileno (mobile phone number), phoneResidence, address, nicnum (NIC number), dateOfBirth (DOB), appointmentDate, designation, divisioncode, salarycode.
    Maps to GET /api/employees/fullname/{name}."""
    return make_request(f"/api/employees/fullname/{name}")

@tool
def fetchEmployeeByName(name: str) -> list:
    """Primary tool to search for an employee by name or full name (case-insensitive match).
    Use when a person's name is mentioned in the prompt, or when looking up employee contact info, mobile phone number, phoneResidence, residential address, NIC number (nicnum), email, designation, or division.
    Returns complete employee records containing: empno (Employee Number), fullname, email, mobileno (mobile phone number), phoneResidence, address, nicnum (NIC number), dateOfBirth (DOB), designation, divisioncode, salarycode.
    Maps to GET /api/employees/fullname/{name}."""
    return make_request(f"/api/employees/fullname/{name}")

@tool
def fetchEmployeeByFullname(fullname: str) -> list:
    """Primary tool to search for an employee by full name (case-insensitive match).
    Use when a person's full name is mentioned in the prompt, or when looking up employee contact info, mobile phone number, phoneResidence, residential address, NIC number (nicnum), email, designation, or division.
    Returns complete employee records containing: empno (Employee Number), fullname, email, mobileno (mobile phone number), phoneResidence, address, nicnum (NIC number), dateOfBirth (DOB), designation, divisioncode, salarycode.
    Maps to GET /api/employees/fullname/{fullname}."""
    return make_request(f"/api/employees/fullname/{fullname}")

@tool
def fetchEmployeesByTitle(title: str) -> list:
    """Retrieves employee records filtered by salutation Title (e.g. 'Mr', 'Miss', 'Mrs', 'Dr', 'Prof', 'Eng').
    Maps to GET /api/employees/title/{title}."""
    return make_request(f"/api/employees/title/{title}")

@tool
def fetchEmployeesByGender(gender: str) -> list:
    """Retrieves employee records filtered by Gender ('Male' or 'Female').
    Maps to GET /api/hr-personal-details/gender/{gender} (canonical) or GET /api/employees/gender/{gender}."""
    if not gender:
        return {"error": "gender cannot be empty"}
    res = make_request(f"/api/hr-personal-details/gender/{quote(str(gender))}")
    if isinstance(res, list) and res:
        return res
    fallback = make_request(f"/api/employees/gender/{quote(str(gender))}")
    if isinstance(fallback, list) and fallback:
        return fallback
    return res if isinstance(res, list) else fallback

@tool
def fetchEmployeesByMobileno(mobileno: str) -> list:
    """Retrieves employee records matching a mobile telephone contact number.
    Maps to GET /api/employees/mobileno/{mobileno}."""
    return make_request(f"/api/employees/mobileno/{mobileno}")

@tool
def fetchEmployeesByDivisioncode(divisioncode: str) -> list:
    """Retrieves all employee records belonging to a specific division.
    Arguments & Foreign Key:
    - divisioncode (str/int) [FOREIGN KEY]: Numeric division code, short acronym, or division name (e.g. 'COM', 'IT', 'ITD', 5, 9) linking to 'divisioncode' in 'division'.
    Uses division endpoints (/api/divisions/{divisioncode}, /api/divisions/shcode/{shCode}, /api/divisions/name/{name}) and /api/employees.
    Returns complete employee records including full names, designations, contacts, and division details."""
    from aria_agent.tools.division import resolve_division_code
    code_int = resolve_division_code(divisioncode)
    cleaned = str(code_int) if code_int is not None else clean_id(divisioncode)
    if not cleaned:
        return {"error": "divisioncode cannot be empty"}

    # 1. Fetch official division identity via division endpoints (/api/divisions)
    div_info = None
    if code_int is not None:
        div_info = make_request(f"/api/divisions/{code_int}")
    if not isinstance(div_info, dict) or "error" in div_info:
        div_info = make_request(f"/api/divisions/shcode/{cleaned}")
    if not isinstance(div_info, dict) or "error" in div_info:
        div_info = make_request(f"/api/divisions/name/{cleaned}")

    eff_code = (div_info.get("divisioncode") if isinstance(div_info, dict) else None) or code_int

    # 2. Retrieve all employee records matching this division from /api/employees
    all_emp = _get_all_employees_cached()
    if isinstance(all_emp, list) and all_emp:
        matched = []
        for r in all_emp:
            if not isinstance(r, dict):
                continue
            r_div_code = r.get("divisioncode") or r.get("divisionCode")
            r_div_obj = r.get("division") if isinstance(r.get("division"), dict) else {}
            nested_code = r_div_obj.get("divisioncode")
            nested_sh = str(r_div_obj.get("shCode") or "").strip().lower()
            nested_name = str(r_div_obj.get("division") or "").strip().lower()

            if eff_code is not None and (
                r_div_code == eff_code
                or str(r_div_code) == str(eff_code)
                or nested_code == eff_code
                or str(nested_code) == str(eff_code)
            ):
                matched.append(r)
            elif cleaned and (
                str(r_div_code) == str(cleaned)
                or (nested_sh and nested_sh == str(cleaned).lower())
                or (nested_name and str(cleaned).lower() in nested_name)
            ):
                matched.append(r)

        if matched:
            return matched

    # 3. Fallback: If division exists but employee catalog returned empty, extract division leadership
    if isinstance(div_info, dict) and "error" not in div_info:
        leaders = []
        for role_key in ("headOfDivision", "deputyDirectorGeneral", "directorGeneral"):
            leader = div_info.get(role_key)
            if isinstance(leader, dict) and leader.get("empno"):
                leaders.append(leader)
        if leaders:
            return leaders

    return []

@tool
def fetchEmployeesByDesigcode(desigcode: str) -> list:
    """Retrieves all employee records holding a specific designation.
    Arguments & Foreign Key:
    - desigcode (str/int) [FOREIGN KEY]: Numeric designation code linking to 'desigcode' in 'hr_designation_tbl'.
    Maps to GET /api/employees and GET /api/hr-official-details/designation/{desigcode}."""
    cleaned = clean_id(desigcode)
    if not cleaned:
        return {"error": "desigcode cannot be empty"}
    all_emp = _get_all_employees_cached()
    if isinstance(all_emp, list) and all_emp:
        matched = [
            r for r in all_emp
            if isinstance(r, dict) and (
                str(r.get("desigcode") or "") == str(cleaned)
                or (isinstance(r.get("designation"), dict) and str(r.get("designation", {}).get("desigcode") or "") == str(cleaned))
            )
        ]
        if matched:
            return matched
    res = make_request(f"/api/hr-official-details/designation/{cleaned}")
    if isinstance(res, list) and res:
        names_map = _get_names_map()
        if names_map:
            for rec in res:
                if isinstance(rec, dict):
                    e_no = clean_id(rec.get("empNo") or rec.get("empno"))
                    if e_no and e_no in names_map:
                        rec["fullname"] = names_map[e_no]
        return res
    return []

@tool
def fetchEmployeesByEmptypecode(emptypecode: str) -> list:
    """Retrieves all employee records matching a specific employment type code (emptypecode).
    Arguments & Foreign Key:
    - emptypecode (str/int) [FOREIGN KEY]: Employment type code.
    Maps to GET /api/employees/emptypecode/{emptypecode}."""
    return make_request(f"/api/employees/emptypecode/{emptypecode}")

@tool
def fetchEmployeesByCategorycode(categorycode: str) -> list:
    """Retrieves all employee records belonging to a specific staff category code.
    Arguments & Foreign Key:
    - categorycode (str/int) [FOREIGN KEY]: Staff category code linking to 'categorycode' in 'category'.
    Maps to GET /api/employees and GET /api/hr-official-details/category/{categorycode}."""
    cleaned = clean_id(categorycode)
    if not cleaned:
        return {"error": "categorycode cannot be empty"}
    all_emp = _get_all_employees_cached()
    if isinstance(all_emp, list) and all_emp:
        matched = [
            r for r in all_emp
            if isinstance(r, dict) and (
                str(r.get("categorycode") or "") == str(cleaned)
                or (isinstance(r.get("category"), dict) and str(r.get("category", {}).get("categorycode") or "") == str(cleaned))
            )
        ]
        if matched:
            return matched
    res = make_request(f"/api/hr-official-details/category/{cleaned}")
    if isinstance(res, list) and res:
        names_map = _get_names_map()
        if names_map:
            for rec in res:
                if isinstance(rec, dict):
                    e_no = clean_id(rec.get("empNo") or rec.get("empno"))
                    if e_no and e_no in names_map:
                        rec["fullname"] = names_map[e_no]
        return res
    return []

@tool
def fetchEmployeesByStatus(status: str) -> list:
    """Retrieves employee records filtered by employment status ('Active', 'Retired', 'Resigned').
    Maps to GET /api/employees and GET /api/hr-official-details/active/{status}."""
    if not status:
        return {"error": "status cannot be empty"}
    all_emp = _get_all_employees_cached()
    if isinstance(all_emp, list) and all_emp:
        matched = [
            r for r in all_emp
            if isinstance(r, dict) and (
                str(r.get("status") or "").strip().lower() == str(status).strip().lower()
            )
        ]
        if matched:
            return matched
    res = make_request(f"/api/hr-official-details/active/{quote(str(status))}")
    if isinstance(res, list) and res:
        return res
    return []

@tool
def fetchEmployeesByAddress(address: str) -> list:
    """Retrieves employee records matching a partial or full residential address.
    Maps to GET /api/employees/address/{address}."""
    return make_request(f"/api/employees/address/{address}")

@tool
def fetchEmployeesByMaritalstatus(maritalstatus: str) -> list:
    """Retrieves employee records filtered by marital status ('Single', 'Married').
    Maps to GET /api/employees/maritalstatus/{maritalstatus}."""
    return make_request(f"/api/employees/maritalstatus/{maritalstatus}")

@tool
def fetchEmployeesByGrade(grade: str) -> list:
    """Retrieves employee records filtered by salary grade (e.g. 'Grade I', 'Grade II', 'Grade III').
    Maps to GET /api/employees/grade/{grade}."""
    return make_request(f"/api/employees/grade/{grade}")

@tool
def fetchEmployeeByEmpNo(empno: str) -> Any:
    """Retrieves full employee record by Employee Number (empNo [FK]).
    Maps to GET /api/employees/empno/{empno}."""
    return fetchEmployeeByEmpno.func(empno)
