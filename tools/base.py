"""Base OOP abstractions and factory utilities for REST API tools."""

from typing import Callable, Any, Optional
from langchain_core.tools import tool, BaseTool
from aria_agent.http.client import make_request, clean_id


class BaseApiEndpointTool:
    """Encapsulates common endpoint fetching, ID sanitization, and error handling logic."""

    def __init__(self, endpoint_prefix: str, entity_name: str):
        self.endpoint_prefix = endpoint_prefix.rstrip('/')
        self.entity_name = entity_name

    def fetch_all(self) -> list:
        """Fetch all records for this entity."""
        return make_request(self.endpoint_prefix)

    def fetch_by_id(self, id_val: str) -> dict:
        """Fetch a specific record by its unique ID."""
        cleaned = clean_id(id_val)
        if not cleaned:
            return {"error": f"Invalid {self.entity_name} ID format: {id_val}"}
        return make_request(f"{self.endpoint_prefix}/{cleaned}")

    def fetch_by_field(self, field_name: str, value: str) -> Any:
        """Fetch records by a specific field path."""
        if not value or not str(value).strip():
            return {"error": f"{self.entity_name} {field_name} cannot be empty"}
        return make_request(f"{self.endpoint_prefix}/{field_name}/{value}")
