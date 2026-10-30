"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrProjects() -> list:
    """."""


@tool
def fetchHrProjectsByYear(year: int) -> list:
    """Retrieves HR projects filtered by initiation year."""


@tool
def fetchHrProjectsByProjectType(ptCode: int) -> list:
    """Retrieves HR projects filtered strictly by numeric project type code (ptCode)."""


@tool
def fetchHrProjectsByCode(code: str) -> list:
    """Retrieves HR project details matching a specific unique project code."""


@tool
def fetchHrProjectsByProjectName(pname: str) -> list:
    """Retrieves HR projects matching a full or partial project title/name."""


@tool
def fetchHrProjectsByApCode(apcode: str) -> list:
    """Retrieves HR projects filtered by approval/accounting code (apcode)."""


@tool
def fetchHrProjectsByPType(ptype: str) -> list:
    """Retrieves HR projects filtered strictly by official project classification type
    description/name."""


@tool
def fetchHrProjectsByClient(cname: str) -> list:
    """Retrieves HR projects funded by, sponsored by, or executed for an external client, sponsor,
    customer, or partner organization. Use this tool whenever the user asks for HR projects
    related to, funded by, or sponsored by an external client, sponsor, partner institution,
    ministry, or government department. Searches against client/sponsor name (cname). Supports
    full or partial organization names."""


@tool
def fetchHrProjectsByStatus(confirm: str) -> list:
    """Retrieves HR projects filtered by confirmation status."""


@tool
def fetchHrProjectsBySkillCode(skCode: str) -> list:
    """Retrieves HR projects filtered by technical skill category code (skCode)."""


@tool
def fetchHrProjectsByClosedStatus(pClose: str) -> list:
    """Retrieves HR projects filtered by closure status."""


@tool
def fetchHrProjectsByEmployee(empNo: str) -> list:
    """Retrieves all HR projects assigned to or created by a specific employee."""
