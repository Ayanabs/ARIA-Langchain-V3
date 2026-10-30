from typing import Any
from langchain_core.tools import tool
from urllib.parse import quote
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQAL() -> list:
    """Retrieves G.C.E. Advanced Level (A/L) examination results for all employees from GET /api/hr-q-al.
    Database & JSON fields returned per record:
    - hr_q_alid (int): Primary key row identifier for A/L result.
    - EmpNo / empNo (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - ALIndex / aLIndex (str): G.C.E. Advanced Level Examination Index Number.
    - ALSubNo / aLSubNo (str/int) [FOREIGN KEY]: A/L Subject Code/Number (linking to 'Sub_No' in 'hr_q_al_subjects').
    - ALSubGrade / aLSubGrade (str): Subject Grade achieved ('A', 'B', 'C', 'S', 'F').
    - ALYear / aLYear (str/int): Year G.C.E. A/L examination was sat (e.g. '2013').
    Maps to GET /api/hr-q-al."""
    return make_request("/api/hr-q-al")

@tool
def fetchHrQALByEmployeeNo(empNo: str) -> list:
    """Retrieves G.C.E. Advanced Level (A/L) examination subject results for an employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: EmpNo [FK], ALIndex (index number), ALSubNo [FK] (subject code), ALSubGrade (grade: A, B, C, S), ALYear (exam year).
    Use when asked about an employee's A/L results, Advanced Level subjects, school A/L grades, or educational qualifications.
    Maps to GET /api/hr-q-al/employee/{empNo}."""
    if not empNo or not str(empNo).strip():
        return {"error": "Employee number cannot be empty"}

    return make_request(
        f"/api/hr-q-al/employee/{quote(empNo)}"
    )

@tool
def fetchHrQALByALIndex(aLIndex: str) -> list:
    """Retrieves A/L examination records filtered by G.C.E. Advanced Level Examination Index Number (aLIndex).
    Returns fields including EmpNo [FK], ALIndex, ALSubNo [FK], ALSubGrade, ALYear.
    Maps to GET /api/hr-q-al/index/{aLIndex}."""
    if not aLIndex or not str(aLIndex).strip():
        return {"error": "AL index cannot be empty"}

    return make_request(
        f"/api/hr-q-al/index/{quote(aLIndex)}"
    )

@tool
def fetchHrQALByALSubNo(aLSubNo: str) -> list:
    """Retrieves A/L examination records filtered by Subject Number/Code (aLSubNo).
    Arguments & Foreign Key:
    - aLSubNo (str/int) [FOREIGN KEY]: Subject Code linking to 'Sub_No' in 'hr_q_al_subjects'.
    Maps to GET /api/hr-q-al/sub-no/{aLSubNo}."""
    if not aLSubNo or not str(aLSubNo).strip():
        return {"error": "AL subject number cannot be empty"}

    return make_request(
        f"/api/hr-q-al/sub-no/{quote(aLSubNo)}"
    )

@tool
def fetchHrQALByALSubGrade(aLSubGrade: str) -> list:
    """Retrieves A/L examination records filtered by Subject Grade (aLSubGrade, e.g. 'A', 'B', 'C', 'S').
    Maps to GET /api/hr-q-al/sub-grade/{aLSubGrade}."""
    if not aLSubGrade or not str(aLSubGrade).strip():
        return {"error": "AL subject grade cannot be empty"}

    return make_request(
        f"/api/hr-q-al/sub-grade/{quote(aLSubGrade)}"
    )

@tool
def fetchHrQALByALYear(aLYear: str) -> list:
    """Retrieves A/L examination records filtered by examination year (aLYear, e.g. '2013', '2015').
    Maps to GET /api/hr-q-al/year/{aLYear}."""
    cleaned = clean_id(aLYear)

    if not cleaned:
        return {"error": f"Invalid AL year format: {aLYear}"}

    return make_request(
        f"/api/hr-q-al/year/{cleaned}"
    )

@tool
def fetchHrQALByEmpNo(empNo: str) -> Any:
    """Retrieves G.C.E. Advanced Level (A/L) exam subject results and educational qualifications for an employee by Employee Number (empNo [FK]).
    Maps to GET /api/hr-q-al/employee/{empNo}."""
    return fetchHrQALByEmployeeNo.func(empNo)

