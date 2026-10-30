"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrPersonalDetails() -> list:
    """Retrieves extended personal records for all employees."""


@tool
def fetchHrPersonalDetailsByEmpNo(empNo: int) -> dict:
    """Retrieves extended personal information for a specific employee by Employee Number (empNo)."""


@tool
def fetchHrPersonalDetailsByTitle(title: str) -> list:
    """Retrieves personal records for ALL employees filtered by salutation Title."""


@tool
def fetchHrPersonalDetailsBySurname(surname: str) -> list:
    """Retrieves personal records for ALL employees matching a specific Surname / Last Name."""


@tool
def fetchHrPersonalDetailsByInitials(initials: str) -> list:
    """Retrieves personal records for ALL employees matching specific Name Initials."""


@tool
def fetchHrPersonalDetailsByFullname(fullname: str) -> list:
    """Retrieves personal records for employees matching a full name denoted by initials (NameDnbyIntl)
    in the HR personal records table. Note: For general employee searches, contact info, mobile
    number, phone, or address by name, prefer fetchEmployeeByName or fetchEmployeesByFullname as
    the primary tool. Use this tool only when searching specific HR personal records when empNo
    is not yet known."""


@tool
def fetchHrPersonalDetailsByGender(gender: str) -> list:
    """Retrieves personal records for ALL employees filtered by Gender."""
