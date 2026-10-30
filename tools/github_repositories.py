"""Registered tools. Endpoints and keys are bound in config/tools.yaml."""

from aria.catalog import tool


@tool
def list_repositories() -> list:
    """Retrieves repositories for a GitHub organization or user account via the Spring Boot GitHub App
    Adapter."""
