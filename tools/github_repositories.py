"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def list_repositories() -> list:
    """Lists repositories for a GitHub organization or user account, returning name,
    description, language, and owner."""
