"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmployees() -> list:
    """Lists complete employee master records, returning ID, number, title, full name, email,
    and mobile number."""


@tool
def fetchAllEmployeeNames() -> list:
    """Lists lightweight employee name records, returning employee number, full name, and name
    with initials."""


@tool
def fetchEmployeeByEmail(email: str) -> dict:
    """Gets one employee record selected by work email address, returning full name, mobile
    number, email, and designation code."""


@tool
def fetchEmployeeByNicnum(nicnum: str) -> dict:
    """Gets one employee record selected by national identity card number, returning full name,
    mobile number, email, and designation code."""


@tool
def fetchEmployeesByPhone(phone: str) -> list:
    """Lists employee records selected by phone number, returning id, empno, fullname, and
    email."""


@tool
def fetchEmployeesByFullname(fullname: str) -> list:
    """Lists employee records selected by full name, returning full name, mobile number, email,
    and designation code."""


@tool
def fetchEmployeesByName(name: str) -> list:
    """Lists employee records selected by name, returning full name, mobile number, email, and
    designation code."""


@tool
def fetchEmployeeByName(name: str) -> list:
    """Lists employee records selected by name, returning full name, mobile number, email, and
    designation code."""


@tool
def fetchEmployeeByFullname(fullname: str) -> list:
    """Lists employee records selected by full name, returning full name, mobile number, email,
    and designation code."""


@tool
def fetchEmployeesByDesigcode(desigcode: int) -> list:
    """Lists employee records selected by designation code, returning employee number,
    appointment date, division code, and category code."""


@tool
def fetchEmployeesByCategorycode(categorycode: str) -> list:
    """Lists employee records selected by staff category code, returning employee number,
    appointment date, division code, and designation code."""


@tool
def fetchEmployeesByStatus(status: str) -> list:
    """Lists employee records selected by employment status, returning emp no, dateof
    appoinment, division code, and category."""


@tool
def fetchEmployeeByEmpno(empno: int) -> dict:
    """Gets one employee record selected by employee number, returning full name, mobile number,
    email, and designation code."""
