from typing import Any
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQOL() -> list:
    """Retrieves G.C.E. Ordinary Level (O/L) examination results for all employees from GET /api/hr-q-ol.
    Database & JSON fields returned per record:
    - hr_ol_qid (int): Primary key row identifier for O/L result.
    - empNo / emp_no (str/int) [FOREIGN KEY]: Employee Number (linking to 'empno' in 'employee').
    - olIndex (str): G.C.E. Ordinary Level Examination Index Number.
    - olSubNo (str/int) [FOREIGN KEY]: O/L Subject Code/Number (linking to 'Sub_No' in 'hr_q_olsubjects').
    - olSubName (str): O/L Subject Name (e.g. Mathematics, Science, English, Sinhala).
    - olSubGrade (str): Grade achieved ('A', 'B', 'C', 'S', 'W', Distinction, Credit, Pass).
    - olYear (str/int): Year G.C.E. O/L examination was sat (e.g. '2011').
    Maps to GET /api/hr-q-ol."""
    return make_request("/api/hr-q-ol")

@tool
def fetchHrQOLByEmployeeNo(empNo: str) -> list:
    """Retrieves G.C.E. Ordinary Level (O/L) examination subject results for an employee by Employee Number (empNo).
    Arguments & Foreign Key:
    - empNo (str/int) [FOREIGN KEY]: Employee Number linking to 'empno' in 'employee'.
    Returns fields: empNo [FK], olSubName (e.g. Mathematics, Science, English), olSubGrade (A, B, C, S), olYear (exam year), olIndex (index number).
    Use when asked about an employee's O/L results, O/L subjects, Ordinary Level exam grades, or school qualifications.
    Maps to GET /api/hr-q-ol/employee/{empNo}."""
    if not empNo or not str(empNo).strip():
        return {"error": "Employee number cannot be empty"}

    return make_request(
        f"/api/hr-q-ol/employee/{str(empNo).strip()}"
    )

@tool
def fetchHrQOLByEmpNo(empNo: str) -> Any:
    """Retrieves O/L exam subject results for an employee by Employee Number (empNo [FK]).
    Maps to GET /api/hr-q-ol/employee/{empNo}."""
    return fetchHrQOLByEmployeeNo.func(empNo)


@tool
def fetchHrQOLByOLIndex(oLIndex: str) -> list:
    """Retrieves G.C.E. O/L exam records by Candidate Index Number (oLIndex).
    Maps to GET /api/hr-q-ol/index/{oLIndex}."""
    if not oLIndex or not str(oLIndex).strip():
        return {"error": "Index number cannot be empty"}
    return make_request(f"/api/hr-q-ol/index/{str(oLIndex).strip()}")


@tool
def fetchHrQOLByOLSubNo(oLSubNo: str) -> list:
    """Retrieves G.C.E. O/L exam records by Subject Number (oLSubNo [FK]).
    Maps to GET /api/hr-q-ol/sub-no/{oLSubNo}."""
    if not oLSubNo or not str(oLSubNo).strip():
        return {"error": "Subject number cannot be empty"}
    return make_request(f"/api/hr-q-ol/sub-no/{str(oLSubNo).strip()}")


@tool
def fetchHrQOLByOLSubGrade(oLSubGrade: str) -> list:
    """Retrieves G.C.E. O/L exam records by Subject Grade (e.g. 'A', 'B', 'C', 'S').
    Maps to GET /api/hr-q-ol/sub-grade/{oLSubGrade}."""
    if not oLSubGrade or not str(oLSubGrade).strip():
        return {"error": "Grade cannot be empty"}
    return make_request(f"/api/hr-q-ol/sub-grade/{str(oLSubGrade).strip()}")


@tool
def fetchHrQOLByOLYear(oLYear: str) -> list:
    """Retrieves G.C.E. O/L exam records by Examination Year (e.g. '2015').
    Maps to GET /api/hr-q-ol/year/{oLYear}."""
    if not oLYear or not str(oLYear).strip():
        return {"error": "Year cannot be empty"}
    return make_request(f"/api/hr-q-ol/year/{str(oLYear).strip()}")


