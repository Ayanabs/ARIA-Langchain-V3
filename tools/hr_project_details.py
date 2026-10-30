"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def fetchAllHrProjectDetails() -> list:
    """Retrieves detailed HR project activity specifications."""


@tool
def fetchHrProjectDetailsByProjectName(pname: str) -> list:
    """Retrieves detailed HR project specs filtered by project title/name."""


@tool
def fetchHrProjectDetailsByApNumber(apnumber: int) -> list:
    """Retrieves detailed HR project specs filtered by approval code (apnumber)."""


@tool
def fetchHrProjectDetailsByProjectType(ptype: str) -> list:
    """Retrieves detailed HR project specs filtered by project type description (ptype)."""


@tool
def fetchHrProjectDetailsByCompany(cname: str) -> list:
    """Retrieves detailed HR project specs filtered by client or sponsoring company name (cname)."""
