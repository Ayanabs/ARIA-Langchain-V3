from langchain_core.tools import tool
from aria_agent.http.client import make_request


@tool
def fetchUploadedPolicies() -> list:
    """Retrieves the list of uploaded company policy documents, guidelines, and office regulations in the knowledge base.
    Use when asked what policy documents, handbooks, or company guidelines are available.
    Maps to /api/rag/uploaded-policies."""
    return make_request("/api/rag/uploaded-policies")
