"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllEmployees() -> list:
    """Retrieves the authoritative complete master list of all employees in the organisation."""


@tool
def fetchAllEmployeeNames() -> list:
    """Retrieves lightweight name and ID records for all employees."""


@tool
def fetchEmployeeByEmail(email: str) -> dict:
    """Retrieves the full employee record matching a specific work email address."""


@tool
def fetchEmployeeByNicnum(nicnum: str) -> dict:
    """Retrieves an employee record by National Identity Card (NIC) number."""


@tool
def fetchEmployeesByPhone(phone: str) -> list:
    """Retrieves employee records matching a telephone or mobile phone number."""


@tool
def fetchEmployeesByFullname(fullname: str) -> list:
    """Searches for employees by full name (case-insensitive partial match). Primary tool when a
    person's name is mentioned in the prompt, or when searching for employee contact info,
    mobile number, phone, address, NIC number (nicnum), email, designation, or division."""


@tool
def fetchEmployeesByName(name: str) -> list:
    """Searches for employees by name or full name (case-insensitive partial match). Primary tool when
    a person's name is mentioned in the prompt, or when searching for employee contact info,
    mobile number, phone, address, NIC number (nicnum), email, designation, or division."""


@tool
def fetchEmployeeByName(name: str) -> list:
    """Primary tool to search for an employee by name or full name (case-insensitive match). Use when a
    person's name is mentioned in the prompt, or when looking up employee contact info, mobile
    phone number, phoneResidence, residential address, NIC number (nicnum), email, designation,
    or division."""


@tool
def fetchEmployeeByFullname(fullname: str) -> list:
    """Primary tool to search for an employee by full name (case-insensitive match). Use when a
    person's full name is mentioned in the prompt, or when looking up employee contact info,
    mobile phone number, phoneResidence, residential address, NIC number (nicnum), email,
    designation, or division."""


@tool
def fetchEmployeesByDesigcode(desigcode: int) -> list:
    """Retrieves all employee records holding a specific designation."""


@tool
def fetchEmployeesByCategorycode(categorycode: str) -> list:
    """Retrieves all employee records belonging to a specific staff category code."""


@tool
def fetchEmployeesByStatus(status: str) -> list:
    """Retrieves employee records filtered by employment status."""


@tool
def fetchEmployeeByEmpno(empno: int) -> dict:
    """Retrieves one employee's master record by employee number."""
