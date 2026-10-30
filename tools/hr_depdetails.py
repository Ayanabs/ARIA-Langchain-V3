"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrDepDetails() -> list:
    """Lists dependent family member records, returning ID, employee number, relationship, name,
    and birthday."""


@tool
def fetchHrDepDetailsByEmployee(empNo: int) -> list:
    """Lists dependent family member records selected by employee number, returning
    relationship, name, birthday, and idno."""


@tool
def fetchHrDepDetailsByRelationship(relationship: int) -> list:
    """Lists dependent family member records selected by relationship ID, returning emp no,
    name, birthday, and idno."""


@tool
def searchHrDepDetailsByName(name: str) -> list:
    """Lists employee dependent records selected by dependent name, returning employee number,
    relationship, name, and birthday."""
