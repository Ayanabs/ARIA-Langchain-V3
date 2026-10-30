from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id


@tool
def fetchAllHrPersonalDetails() -> list:
    """Retrieves extended personal records for all employees from GET /api/hr-personal-details.
    Database & JSON fields returned per record:
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (unique identifier linking to 'empno' in 'employee').
    - Title / title (str): Salutation Title (e.g. 'Mr', 'Miss', 'Mrs', 'Dr', 'Prof').
    - Surname / surname (str): Employee Surname / Last Name.
    - Initials / initials (str): Employee Name Initials.
    - NameDnbyIntl / fullname (str): Full Name Denoted by Initials.
    - NICNum / nic (str): National Identity Card (NIC) Number.
    - DOB / dateOfBirth (str): Date of Birth (Format: YYYY-MM-DD).
    - Gender / gender (str): Gender ('Male', 'Female').
    - PrmntAdd1, PrmntAdd2, PrmntAdd3 / address (str): Permanent Residential Address Lines.
    - MrtSt / maritalStatus (str): Marital Status ('Single', 'Married').
    - Mob / mobile (str): Mobile Telephone Contact Number.
    Use when asked about employee residential addresses, permanent addresses, NIC, or personal contact details.
    Maps to GET /api/hr-personal-details."""
    return make_request("/api/hr-personal-details")


@tool
def fetchHrPersonalDetailsByEmpNo(empNo: str) -> dict:
    """Retrieves extended personal information for a specific employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields:
    - EmpNo: Employee Number [FK]
    - Title: Salutation Title ('Mr', 'Miss', 'Mrs', 'Dr', 'Prof')
    - Surname: Employee Surname / Last Name
    - Initials: Name Initials
    - NameDnbyIntl: Full Name Denoted by Initials
    - NICNum: National Identity Card (NIC) Number
    - DOB: Date of Birth (YYYY-MM-DD)
    - Gender: Gender ('Male', 'Female')
    - PrmntAdd1, PrmntAdd2, PrmntAdd3: Permanent Residential Address
    - Mob: Mobile Phone Number
    Use when asked about personal profile, NIC number, DOB, marital status, address, or mobile number for a specific employee.
    Maps to GET /api/hr-personal-details/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    return make_request(f"/api/hr-personal-details/{cleaned}")


@tool
def fetchHrPersonalDetailsByTitle(title: str) -> list:
    """Retrieves personal records for ALL employees filtered by salutation Title (e.g. 'Mr', 'Miss', 'Mrs', 'Dr', 'Prof').
    Returns a bulk list of employees with that title. Use ONLY for aggregate/bulk queries (e.g. 'how many employees are Dr.').
    Do NOT use this to look up a specific individual employee's personal details —
    use the tool that accepts a single empNo parameter (individual employee lookup by ID) instead.
    Returns fields including EmpNo [FK], Title, Surname, Initials, NameDnbyIntl (Full Name), NICNum (National Identity Card Number), DOB (Date of Birth), Gender.
    Maps to GET /api/hr-personal-details/title/{title}."""
    if not title or not str(title).strip():
        return {"error": "Title cannot be empty"}

    return make_request(
        f"/api/hr-personal-details/title/{quote(title)}"
    )


@tool
def fetchHrPersonalDetailsBySurname(surname: str) -> list:
    """Retrieves personal records for ALL employees matching a specific Surname / Last Name.
    Returns a bulk list of matching employees. Use ONLY when searching across the organisation by surname.
    Do NOT use this to look up a specific individual employee when you already have their empNo —
    use the tool that accepts a single empNo parameter (individual employee lookup by ID) instead.
    Returns fields including EmpNo [FK], Title, Surname, Initials, NameDnbyIntl (Full Name), NICNum (NIC Number), DOB (Date of Birth), Gender.
    Maps to GET /api/hr-personal-details/surname/{surname}."""
    if not surname or not str(surname).strip():
        return {"error": "Surname cannot be empty"}

    return make_request(
        f"/api/hr-personal-details/surname/{quote(surname)}"
    )


@tool
def fetchHrPersonalDetailsByInitials(initials: str) -> list:
    """Retrieves personal records for ALL employees matching specific Name Initials (e.g. 'A.B.C.').
    Returns a bulk list of matching employees. Use ONLY when searching across the organisation by initials.
    Do NOT use this to look up a specific individual when you already have their empNo —
    use the tool that accepts a single empNo parameter (individual employee lookup by ID) instead.
    Returns fields including EmpNo [FK], Title, Surname, Initials, NameDnbyIntl (Full Name), NICNum (NIC Number), DOB (Date of Birth).
    Maps to GET /api/hr-personal-details/initials/{initials}."""
    if not initials or not str(initials).strip():
        return {"error": "Initials cannot be empty"}

    return make_request(
        f"/api/hr-personal-details/initials/{quote(initials)}"
    )


@tool
def fetchHrPersonalDetailsByFullname(fullname: str) -> list:
    """Retrieves personal records for employees matching a full name denoted by initials (NameDnbyIntl) in the HR personal records table.
    Note: For general employee searches, contact info, mobile number, phone, or address by name, prefer fetchEmployeeByName or fetchEmployeesByFullname as the primary tool.
    Use this tool only when searching specific HR personal records when empNo is not yet known.
    Returns fields including EmpNo [FK], Title, Surname, Initials, NameDnbyIntl (Full Name), NICNum (NIC Number), DOB (Date of Birth), Gender, Address.
    Maps to GET /api/hr-personal-details/fullname/{fullname}."""
    if not fullname or not str(fullname).strip():
        return {"error": "Full name cannot be empty"}

    return make_request(
        f"/api/hr-personal-details/fullname/{quote(fullname)}"
    )


@tool
def fetchHrPersonalDetailsByGender(gender: str) -> list:
    """Retrieves personal records for ALL employees filtered by Gender ('Male' or 'Female').
    Returns a bulk list. Use ONLY for aggregate/bulk queries (e.g. 'how many female employees are there').
    Do NOT use this to look up a specific individual employee —
    use the tool that accepts a single empNo parameter (individual employee lookup by ID) instead.
    Returns fields including EmpNo [FK], Title, Surname, Initials, NameDnbyIntl (Full Name), NICNum (NIC Number), DOB (Date of Birth), Gender.
    Maps to GET /api/hr-personal-details/gender/{gender}."""
    if not gender or not str(gender).strip():
        return {"error": "Gender cannot be empty"}

    return make_request(
        f"/api/hr-personal-details/gender/{quote(gender)}"
    )


