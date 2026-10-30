from typing import Any
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrHigherEduDetails() -> list:
    """Retrieves higher education qualification records for all employees from GET /api/hr-higher-edu-details.
    Database & JSON fields returned per record:
    - id (int): Primary key qualification record ID.
    - emp_no / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - qualificationTitle / degreeName (str): Full title of degree or qualification (e.g. 'BSc in Electrical Engineering', 'MSc in Computer Science').
    - sub_edu_type / subEduType (str): Education category ('Degree', 'Diploma', 'Certificate').
    - higher_edu_level / higherEduLevel (str): Academic level ('Doctorate' [PhD], 'Masters' [MSc/MBA], 'Bachelors' [BSc/BTech], 'Diploma').
    - institute (str): Awarding university or institute.
    - yearObtained (str): Year degree/qualification was obtained.
    Maps to GET /api/hr-higher-edu-details."""
    return make_request("/api/hr-higher-edu-details")

@tool
def fetchHrHighereduDetailsByEmployee(empNo: str) -> list:
    """Retrieves higher education degrees, diplomas, postgraduate, and doctorate qualifications for an employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: empNo [FK], qualificationTitle, degreeName (e.g. 'BSc' [Bachelor of Science], 'MSc' [Master of Science], 'PhD' [Doctor of Philosophy], 'BTech' [Bachelor of Technology], 'MBA' [Master of Business Administration]), institute, higherEduLevel (Bachelors, Masters, Doctorate/PhD, Diploma), yearObtained.
    Use when asked about an employee's degree, masters, PhD, university, or higher education qualifications.
    Maps to GET /api/hr-higher-edu-details/employee/{empNo}."""
    cleaned = clean_id(empNo)

    if not cleaned:
        return {"error": f"Invalid employee number format: {empNo}"}

    return make_request(
        f"/api/hr-higher-edu-details/employee/{cleaned}"
    )

@tool
def fetchHrHighereduDetailsBySubEduType(subEduType: str) -> list:
    """Retrieves higher education records filtered by sub-education category (subEduType, e.g. 'Degree', 'Diploma', 'Certificate').
    Returns fields including emp_no [FK], qualificationTitle, higher_edu_level, institute.
    Maps to GET /api/hr-higher-edu-details/sub-education-type/{subEduType}."""
    if not subEduType or not str(subEduType).strip():
        return {"error": "Sub education type cannot be empty"}

    return make_request(
        f"/api/hr-higher-edu-details/sub-education-type/{subEduType}"
    )

@tool
def fetchHrHighereduDetailsByHigherEduLevel(higherEduLevel: str) -> list:
    """Retrieves higher education records filtered by academic level (higherEduLevel: 'Doctorate' [PhD - Doctor of Philosophy], 'Masters' [MSc - Master of Science / MBA - Master of Business Administration], 'Bachelors' [BSc - Bachelor of Science / BTech - Bachelor of Technology], 'Diploma').
    Maps to GET /api/hr-higher-edu-details/higher-education-level/{higherEduLevel}."""

    if not higherEduLevel or not str(higherEduLevel).strip():
        return {"error": "Higher education level cannot be empty"}

    return make_request(
        f"/api/hr-higher-edu-details/higher-education-level/{higherEduLevel}"
    )

@tool
def fetchHrHighereduDetailsByEmpNo(empNo: str) -> Any:
    """Retrieves higher education qualification records for an employee by Employee Number (empNo [FK]).
    Maps to GET /api/hr-higher-edu-details/employee/{empNo}."""
    return fetchHrHighereduDetailsByEmployee.func(empNo)


