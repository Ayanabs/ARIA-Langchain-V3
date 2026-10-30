"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjects() -> list:
    """Lists all PR projects, returning serial no, year, div code, pt code, description, code,
    pname, apcode, startdate, enddate, ptype, cname, confirm, hod confirm, hod confirmed date,
    sk code, capital, recurrent, externalinput and rdate."""


@tool
def fetchPrProjectBySerialNo(serialNo: int) -> dict:
    """Gets a single project record by its serial number, returning name, description, start
    date, and end date."""


@tool
def fetchPrProjectsByYear(year: int) -> list:
    """Lists projects selected by initiation year, returning serial number, year, description,
    and project name."""


@tool
def fetchPrProjectsByProjectType(ptCode: int) -> list:
    """Lists projects selected by numeric project classification type code, returning serial
    number, year, description, and project name."""


@tool
def fetchPrProjectsByCode(code: str) -> list:
    """Lists projects selected by unique code, returning serial number, project name, client
    name and project type."""


@tool
def fetchPrProjectsByProjectName(pname: str) -> list:
    """Lists projects selected by project name, returning serial number, project name, client
    name and project type."""


@tool
def fetchPrProjectsByApCode(apcode: str) -> list:
    """Lists projects selected by AP code, returning serial number, project name, client name
    and project type."""


@tool
def fetchPrProjectsByPType(ptype: str) -> list:
    """Lists projects selected by project type description, returning serial number, project
    name, client name and project type."""


@tool
def fetchPrProjectsByClient(cname: str) -> list:
    """Lists projects selected by client name, returning serial number, project name, client
    name and project type."""


@tool
def fetchPrProjectsByStatus(confirm: str) -> list:
    """Lists projects selected by confirmation status, returning serial number, year,
    description, and project name."""


@tool
def fetchPrProjectsBySkillCode(skCode: str) -> list:
    """Lists projects selected by technical skill category code, returning serial number, year,
    description, and project name."""


@tool
def fetchPrProjectsByClosedStatus(pClose: str) -> list:
    """Lists projects selected by closure status, returning serial number, project name, client
    name and project type."""


@tool
def fetchPrProjectsByEmployee(empNo: str) -> list:
    """Lists projects selected by employee identifier, returning serial number, project name,
    client name and project type."""
