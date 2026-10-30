"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrPersonalDetails() -> list:
    """Lists extended personal records for employees, returning the employee number, full name,
    gender, date of birth and contact details."""


@tool
def fetchHrPersonalDetailsByEmpNo(empNo: int) -> dict:
    """Gets extended personal information for a specific employee identified by an employee
    number, returning full name, gender, permanent address, and email."""


@tool
def fetchHrPersonalDetailsByTitle(title: str) -> list:
    """Lists employee personal records filtered by title, returning title, surname, initials and
    name."""


@tool
def fetchHrPersonalDetailsBySurname(surname: str) -> list:
    """Lists employee personal records filtered by surname, returning title, surname, initials
    and name."""


@tool
def fetchHrPersonalDetailsByInitials(initials: str) -> list:
    """Lists employee personal records filtered by initials, returning title, surname, initials
    and name."""


@tool
def fetchHrPersonalDetailsByFullname(fullname: str) -> list:
    """Lists personal records for employees matching a specific full name string, returning
    employee number, full name, gender, permanent address, and email."""


@tool
def fetchHrPersonalDetailsByGender(gender: str) -> list:
    """Lists employee personal records filtered by gender, returning title, surname, initials
    and name."""
