"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrProjects() -> list:
    """Lists project records, returning serial number, year, division code, project name, start
    date, end date, type, confirmation status and close status."""


@tool
def fetchHrProjectsByYear(year: int) -> list:
    """Lists HR projects filtered by initiation year, returning serial number, project name,
    description, start date and end date."""


@tool
def fetchHrProjectsByProjectType(ptCode: int) -> list:
    """Lists HR projects selected by numeric project type code, returning serial number, project
    name, description, and type code."""


@tool
def fetchHrProjectsByCode(code: str) -> list:
    """Lists HR projects selected by unique project code, returning serial number, project name,
    description, and start date."""


@tool
def fetchHrProjectsByProjectName(pname: str) -> list:
    """Lists HR projects selected by project title or name, returning serial number, project
    name, description, and start date."""


@tool
def fetchHrProjectsByApCode(apcode: str) -> list:
    """Lists HR projects selected by AP code, returning serial number, project name,
    description, and start date."""


@tool
def fetchHrProjectsByPType(ptype: str) -> list:
    """Lists HR projects selected by official project type description, returning serial number,
    project name, description, and type code."""


@tool
def fetchHrProjectsByClient(cname: str) -> list:
    """Lists HR projects selected by client name, returning serial number, project name,
    description, and client name."""


@tool
def fetchHrProjectsByStatus(confirm: str) -> list:
    """Lists HR projects selected by confirmation status, returning serial number, project name,
    description, and confirmation status."""


@tool
def fetchHrProjectsBySkillCode(skCode: str) -> list:
    """Lists HR projects selected by technical skill category code, returning serial number,
    project name, description, and skill code."""


@tool
def fetchHrProjectsByClosedStatus(pClose: str) -> list:
    """Lists HR projects selected by closure status, returning serial number, project name,
    description, and end date."""


@tool
def fetchHrProjectsByEmployee(empNo: str) -> list:
    """Lists HR projects selected by employee identifier, returning serial number, project name,
    description, and start date."""
