import httpx
from typing import Any
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

from .category import fetchAllCategories
from .claim_type_tbl import fetchAllClaimTypes
from .day_type_tbl import fetchAllDayTypes
from .incomplete_source_tbl import fetchAllIncompleteSources
from .issues_tbl import fetchAllIssues


@tool
def queryPolicyKnowledgeBase(query: str) -> dict:
    """Queries the organisation Policy Knowledge Base vector RAG index for official policies,
    HR guidelines, leave rules, medical claim procedures, reimbursement regulations, office hours,
    dress code, and administrative procedures.
    Use when asked general questions about company policy, guidelines, or rules."""
    from aria_agent.http.client import called_endpoints_var, raw_results_var

    
    endpoint = "/api/policy-knowledge-base"
    
    endpoints = called_endpoints_var.get()
    if isinstance(endpoints, list):
        endpoints.append(endpoint)
        
    from aria_agent.config.config import RAG_SERVICE_URL, RAG_TIMEOUT, logger

    # Query dedicated remote Policy & Knowledge RAG microservice
    rag_url = (RAG_SERVICE_URL or "").strip()
    if rag_url and not (rag_url.endswith("/api/search") or rag_url.endswith("/search") or rag_url.endswith("/ask")):
        rag_url = rag_url.rstrip("/") + "/api/search"
    elif rag_url.endswith("/search") and not rag_url.endswith("/api/search"):
        rag_url = rag_url[:-7] + "/api/search"

    try:
        from aria_agent.http.client import get_sync_client
        req_timeout = RAG_TIMEOUT if RAG_TIMEOUT else 30.0
        client = get_sync_client()
        response = client.post(
            rag_url,
            json={"query": query, "question": query},
            timeout=req_timeout
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                # If remote service returned raw document chunks in 'results', construct 'answer' & 'sources'
                if "results" in data and isinstance(data["results"], list) and not data.get("answer"):
                    import re
                    formatted_chunks = []
                    policy_records = []
                    structured_sources = []
                    for item in data["results"]:
                        if isinstance(item, dict):
                            content = item.get("content", "").strip()
                            metadata = item.get("metadata", {})
                            doc_name = metadata.get("source") or metadata.get("filename") or "Policy Handbook"
                            page_num = metadata.get("page")
                            # Extract section heading if present
                            section = metadata.get("section") or metadata.get("heading") or metadata.get("title")
                            if not section and content:
                                sec_match = re.search(r'(?:^|\n)([0-9]+(?:\.[0-9]+)*\s+[A-Za-z\s]{3,40})', content)
                                if sec_match:
                                    section = sec_match.group(1).strip()
                            if not section:
                                section = f"Page {page_num}" if page_num is not None else "General Policy"

                            source_label = f"{doc_name} (Page {page_num})" if page_num is not None else doc_name
                            
                            citation_item = {
                                "source": doc_name,
                                "document": doc_name,
                                "page": page_num if page_num is not None else 1,
                                "section": section,
                                "content": content
                            }
                            structured_sources.append(citation_item)
                            
                            policy_records.append({
                                "document": doc_name,
                                "page": page_num if page_num is not None else 1,
                                "section": section,
                                "content": content
                            })

                            if content:
                                formatted_chunks.append(f"[{source_label} - {section}]\n{content}")
                        elif isinstance(item, str) and item.strip():
                            formatted_chunks.append(item.strip())
                            rec = {"document": "Policy Handbook", "page": 1, "section": "General", "content": item.strip()}
                            policy_records.append(rec)
                            structured_sources.append({"source": "Policy Handbook", "page": 1, "section": "General", "content": item.strip()})

                    data["answer"] = "\n\n---\n\n".join(formatted_chunks) if formatted_chunks else ""
                    data["sources"] = structured_sources
                    data["records"] = policy_records
                    data["source"] = f"Policy Knowledge Base ({rag_url})"
                elif "answer" not in data and "response" in data:
                    data["answer"] = data["response"]

                results = raw_results_var.get()
                if isinstance(results, list):
                    results.append(data)
                return data
        else:
            err_msg = f"Policy Knowledge Base service at {rag_url} returned status {response.status_code}"
            logger.warning(f"[RAG] {err_msg}: {response.text[:200]}")
            err_data = {"error": err_msg, "answer": err_msg, "sources": [], "records": []}
            results = raw_results_var.get()
            if isinstance(results, list):
                results.append(err_data)
            return err_data
    except Exception as e:
        err_msg = f"Failed to connect to Policy Knowledge Base service at {rag_url}: {str(e)}"
        logger.warning(f"[RAG] {err_msg}")
        err_data = {"error": err_msg, "answer": err_msg, "sources": [], "records": []}
        results = raw_results_var.get()
        if isinstance(results, list):
            results.append(err_data)
        return err_data


@tool
def executeCustomApiRequest(endpoint: str) -> Any:
    """Executes a direct GET request against a custom Spring Boot API endpoint path (e.g. /api/some-endpoint).
    Use only as a fallback when no dedicated tool matches the specific backend endpoint requested."""
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    if not endpoint.startswith("/api"):
        endpoint = "/api" + endpoint
        
    if "chats" in endpoint.lower() or "users" in endpoint.lower():
        return "I don't have enough data to process this request."
        
    try:
        res = make_request(endpoint)
        if not res or (isinstance(res, dict) and "error" in res):
            return "I don't have enough data to process this request."
        return res
    except Exception:
        return "I don't have enough data to process this request."

