"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrProjectDetails() -> list:
    """Lists HR project activity specifications, returning the serial number, project name,
    start date, end date and type code."""


@tool
def fetchHrProjectDetailsByProjectName(pname: str) -> list:
    """Lists project details filtered by project name, returning project name, start date, end
    date and company."""


@tool
def fetchHrProjectDetailsByApNumber(apnumber: int) -> list:
    """Lists project details filtered by AP number, returning project name, start date, end date
    and company."""


@tool
def fetchHrProjectDetailsByProjectType(ptype: str) -> list:
    """Lists project details filtered by project type, returning project name, start date, end
    date and company."""


@tool
def fetchHrProjectDetailsByCompany(cname: str) -> list:
    """Lists project details filtered by company name, returning project name, start date, end
    date and company."""
