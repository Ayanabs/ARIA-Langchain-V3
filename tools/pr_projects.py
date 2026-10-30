"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllPrProjects() -> list:
    """."""


@tool
def fetchPrProjectBySerialNo(serialNo: int) -> dict:
    """Retrieves a single PR project record by primary key serial sequence number (serialNo )."""


@tool
def fetchPrProjectsByYear(year: int) -> list:
    """Retrieves PR projects filtered by initiation year."""


@tool
def fetchPrProjectsByProjectType(ptCode: int) -> list:
    """Retrieves PR projects filtered strictly by numeric project classification type code."""


@tool
def fetchPrProjectsByCode(code: str) -> list:
    """Retrieves PR project details matching a specific unique project code."""


@tool
def fetchPrProjectsByProjectName(pname: str) -> list:
    """Retrieves PR projects matching a full or partial project title/name."""


@tool
def fetchPrProjectsByApCode(apcode: str) -> list:
    """Retrieves PR projects filtered by approval/accounting code (apcode)."""


@tool
def fetchPrProjectsByPType(ptype: str) -> list:
    """Retrieves PR projects filtered strictly by project classification type description/name."""


@tool
def fetchPrProjectsByClient(cname: str) -> list:
    """Retrieves institutional, software, engineering, and research PR projects funded by, sponsored
    by, or executed for an external client, sponsor, customer, or partner organization. Use this
    tool whenever the user asks for projects related to, funded by, or sponsored by an external
    client, sponsor, partner institution, ministry, or government department. Searches against
    client/sponsor name (cname). Supports full or partial organization names."""


@tool
def fetchPrProjectsByStatus(confirm: str) -> list:
    """Retrieves PR projects filtered by confirmation status."""


@tool
def fetchPrProjectsBySkillCode(skCode: str) -> list:
    """Retrieves PR projects filtered by technical skill category code (skCode)."""


@tool
def fetchPrProjectsByClosedStatus(pClose: str) -> list:
    """Retrieves PR projects filtered by closure status."""


@tool
def fetchPrProjectsByEmployee(empNo: str) -> list:
    """Retrieves all PR projects created by, assigned to, or closed by a specific employee."""
