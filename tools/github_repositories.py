"""GitHub Organization & Repositories API Tools for ARIA LangChain Agent (Spring Boot GitHub App Adapter Integration).

Endpoints for interacting with GitHub organization resources via GitHub App:
- GET /api/github/repos/{owner}/{repo}: Get repository details (get_repository, get_owner_repository)
- GET /api/github/repos/{owner}/{repo}/issues: List repository issues (list_repository_issues)
- GET /api/github/repos/{owner}/{repo}/branches: List repository branches (list_repository_branches)
- GET /api/github/repos/{owner}/{repo}/languages: List repository languages (list_repository_languages, get_repository_languages)
- GET /api/github/repos/{owner}/{repo}/contributors: List repository contributors (list_repository_contributors)
- GET /api/github/repos/contributors: List contributors for each repository (list_contributors_for_each_repository)
- GET /api/github/repos/{owner}/{repo}/commits: List repository commits (list_repository_commits)
- GET /api/github/repos/{owner}/{repo}/branches/{branch}/commits: List branch commits (list_branch_commits)
- GET /api/github/repos/{owner}/{repo}/commit-messages: List repository commit messages (list_repository_commit_messages)
- GET /api/github/repos/{owner}/{repo}/branches/{branch}/commit-messages: List branch commit messages (list_branch_commit_messages)
- GET /api/github/repos: List repositories (list_repositories)
- GET /api/github/orgs/{org}/repos: List repositories for an organization (list_org_repositories)
- GET /api/github/orgs/{org}/members: List organization members (list_org_members)
- GET /api/github/members: List organization members (list_members)
"""

import os
import re
import time
from typing import Annotated, Any, Optional, Dict, List
from aria_agent.schemas.retrieval import OptionalReadLimit
from urllib.parse import quote
from langchain_core.tools import tool
from aria_agent.http.client import make_request
from aria_agent.config.config import GITHUB_ORG

_ORG_REPOS_CACHE: Dict[str, Any] = {}


@tool
def search_repositories(
    name: Annotated[str, "Repository name to discover across authorized sources"],
) -> Any:
    """Find accessible repositories by name and return their canonical names, owners and default branches.

    Resolve an informal repository name before related repository reads. Keep
    ambiguous matches separate; owner and repository must come from one result.
    The deployment contract supplies the authenticated API endpoint.
    """
    from aria_agent.services.python_tool_contracts import invoke_python_contract
    return invoke_python_contract("search_repositories", {"name": name})


@tool
def get_repository_tree(owner: str, repo: str, ref: str) -> Any:
    """Retrieve the complete file and folder tree for a verified repository and branch or commit reference.

    Returns path, type, sha and size for each tree entry. Use canonical owner
    and repository values returned by discovery and a retrieved branch/ref.
    This retrieves structure only, without reading file contents.
    The deployment contract supplies the authenticated API endpoint.
    """
    from aria_agent.services.python_tool_contracts import invoke_python_contract
    return invoke_python_contract("get_repository_tree", {"owner": owner, "repo": repo, "ref": ref})


def _clean_repo_identifier(val: Any) -> str:
    """Sanitizes repository name or owner string preserving alphanumeric, hyphens, underscores, and dots.
    Converts whitespace to underscores and strips trailing entity nouns (repos, repo, repository, codebase).
    """
    if val is None:
        return ""
    s = str(val).strip()
    # Strip trailing entity nouns (e.g. 'aria langchain repos' -> 'aria langchain')
    s = re.sub(r"\b(repos|repo|repositories|repository|codebases|codebase)\b\s*$", "", s, flags=re.IGNORECASE).strip()
    # Replace spaces or multiple consecutive whitespace with underscores
    s = re.sub(r"\s+", "_", s)
    # Remove any character not in [a-zA-Z0-9_.-]
    s = re.sub(r"[^a-zA-Z0-9_.-]", "", s)
    return s.strip("._-")


def _get_org_repo_names(owner: str) -> List[str]:
    """Retrieves and caches repository names for the organization (5-minute TTL)."""
    from aria_agent.services.request_read_cache import cached_value, remember_value
    owner_key = (owner or "").strip().lower()
    if not owner_key:
        return []
    cached = cached_value(("repository_names", owner_key))
    if cached is not None:
        return cached

    names: List[str] = []
    try:
        res = make_request(f"/api/github/orgs/{quote(owner, safe='')}/repos", query_params={"limit": 100})
        if isinstance(res, list):
            for item in res:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item["name"]))
    except Exception:
        pass

    if not names:
        try:
            from aria_agent.services.github_service import get_github_service
            direct = get_github_service()
            d_res = direct.list_repositories(org=owner, limit=100)
            if isinstance(d_res, list):
                for item in d_res:
                    if isinstance(item, dict) and item.get("name"):
                        names.append(str(item["name"]))
        except Exception:
            pass

    if names:
        remember_value(("repository_names", owner_key), names)
    return names


def _resolve_canonical_repo(owner: str, repo: str) -> str:
    """Resolves raw, lowercased, spaced, or natural-language repository names against known repositories in the organization."""
    clean = _clean_repo_identifier(repo)
    if not clean:
        return ""

    # Strip conversational suffixes like " repos" or " repo"
    clean = re.sub(r"\s+repos?$", "", clean, flags=re.IGNORECASE).strip()

    owner_key = (owner or "").strip().lower()
    from aria_agent.services.request_read_cache import cached_value
    cached = cached_value(("repository_names", owner_key))
    has_spaces_or_special = bool(re.search(r"[\s]", clean))

    known: List[str] = []
    if cached is not None:
        known = cached
    elif has_spaces_or_special:
        known = _get_org_repo_names(owner)

    if not known:
        return clean

    # 1. Exact or case-insensitive match
    for k in known:
        if k.lower() == clean.lower():
            return k

    # 2. Match ignoring all delimiters/underscores/hyphens
    norm_target = re.sub(r"[^a-zA-Z0-9]", "", clean).lower()
    for k in known:
        if re.sub(r"[^a-zA-Z0-9]", "", k).lower() == norm_target:
            return k

    # 3. Match without prefix or suffix
    for k in known:
        k_norm = re.sub(r"[^a-zA-Z0-9]", "", k).lower()
        if (len(norm_target) >= 4 and k_norm.endswith(norm_target)) or (len(k_norm) >= 4 and norm_target.endswith(k_norm)):
            return k

    return clean




@tool
def list_repositories(
    org: Optional[str] = None,
    type: Optional[str] = "all",
    sort: Optional[str] = "updated",
    direction: Optional[str] = None,
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Retrieves repositories for a GitHub organization or user account via the Spring Boot GitHub App Adapter.

    Arguments:
    - org (str, optional): Target GitHub organization or user account login (e.g. '<your-org-login>' or user login). Defaults to configured GITHUB_ORG.
    - type (str, optional): Repository type filter ('all', 'public', 'private', 'forks', 'sources', 'member'). Default: 'all'.
    - sort (str, optional): Sort field ('created', 'updated', 'pushed', 'full_name'). Default: 'updated'.
    - direction (str, optional): Sort direction ('asc' for ascending, 'desc' for descending).
    - limit (int, optional): Maximum number of repositories to return per page (e.g. 10, 30, 100).
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Maps to Spring Boot: GET /api/github/repos
    Use when asked to list, show, find, browse, or search GitHub repositories or codebases for an organization or account.
    """
    params: Dict[str, Any] = {}
    target_org = org.strip() if org and str(org).strip() else (GITHUB_ORG.strip() if GITHUB_ORG else None)
    if target_org:
        params["org"] = target_org
    if type and str(type).strip():
        params["type"] = str(type).strip()
    if sort and str(sort).strip():
        params["sort"] = str(sort).strip()
    if direction and str(direction).strip():
        params["direction"] = str(direction).strip()
    if limit is not None:
        try:
            params["limit"] = int(limit)
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    res = make_request("/api/github/repos", query_params=params if params else None)
    if isinstance(res, dict) and "error" in res:
        try:
            from aria_agent.services.github_service import get_github_service
            direct_service = get_github_service()
            direct_res = direct_service.list_repositories(org=target_org, limit=limit or 100, repo_type=type or "all")
            if isinstance(direct_res, list) and len(direct_res) > 0:
                return direct_res
            if isinstance(direct_res, list) and len(direct_res) == 0:
                from aria_agent.config.config import GITHUB_TOKEN
                if not GITHUB_TOKEN:
                    backend_err = res.get("detail") or res.get("error")
                    return {
                        "error": (
                            f"Backend adapter unavailable ({backend_err}). "
                            f"Direct GitHub API found 0 public repositories for '{target_org or 'organization'}'. "
                            "If repositories are private, please configure GITHUB_TOKEN in ARIA's .env file or set GITHUB_APP_ID in Spring Boot."
                        ),
                        "backend_error": backend_err,
                        "direct_repositories_found": 0,
                    }
                return direct_res
            if isinstance(direct_res, dict) and direct_res.get("error"):
                backend_err = res.get("detail") or res.get("error")
                return {
                    "error": (
                        f"GitHub repositories could not be retrieved from the backend adapter ({backend_err}). "
                        f"Direct GitHub API access: {direct_res.get('error')}. "
                        "To resolve, configure GITHUB_APP_ID in Spring Boot or set GITHUB_TOKEN in the agent's .env file."
                    ),
                    "backend_error": backend_err,
                    "direct_error": direct_res.get("error"),
                }
        except Exception:
            pass
    return res


@tool
def list_org_repositories(
    org: Optional[str] = None,
    type: Optional[str] = "all",
    sort: Optional[str] = "updated",
    direction: Optional[str] = None,
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Retrieves repositories for the GitHub organization specified in the URL path via the Spring Boot GitHub App Adapter.

    Arguments:
    - org (str, optional): Target GitHub organization login specified in the URL path (e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG if omitted.
    - type (str, optional): Repository type filter ('all', 'public', 'private', 'forks', 'sources', 'member'). Default: 'all'.
    - sort (str, optional): Sort field ('created', 'updated', 'pushed', 'full_name'). Default: 'updated'.
    - direction (str, optional): Sort direction ('asc' or 'desc').
    - limit (int, optional): Maximum number of repositories to return per page.
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Maps to Spring Boot: GET /api/github/orgs/{org}/repos
    Use when querying repositories specifically under a designated organization path.
    """
    clean_org = _clean_repo_identifier(org) if org and str(org).strip() else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_org:
        return {"error": "Organization name is required."}

    params: Dict[str, Any] = {}
    if type and str(type).strip():
        params["type"] = str(type).strip()
    if sort and str(sort).strip():
        params["sort"] = str(sort).strip()
    if direction and str(direction).strip():
        params["direction"] = str(direction).strip()
    if limit is not None:
        try:
            params["limit"] = int(limit)
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    res = make_request(f"/api/github/orgs/{quote(clean_org, safe='')}/repos", query_params=params if params else None)
    if isinstance(res, dict) and "error" in res:
        try:
            from aria_agent.services.github_service import get_github_service
            direct_service = get_github_service()
            direct_res = direct_service.list_repositories(org=clean_org, limit=limit or 100, repo_type=type or "all")
            if isinstance(direct_res, list) and len(direct_res) > 0:
                return direct_res
            if isinstance(direct_res, list) and len(direct_res) == 0:
                from aria_agent.config.config import GITHUB_TOKEN
                if not GITHUB_TOKEN:
                    backend_err = res.get("detail") or res.get("error")
                    return {
                        "error": (
                            f"Backend adapter unavailable ({backend_err}). "
                            f"Direct GitHub API found 0 public repositories for '{clean_org}'. "
                            "If repositories are private, please configure GITHUB_TOKEN in ARIA's .env file or set GITHUB_APP_ID in Spring Boot."
                        ),
                        "backend_error": backend_err,
                        "direct_repositories_found": 0,
                    }
                return direct_res
            if isinstance(direct_res, dict) and direct_res.get("error"):
                backend_err = res.get("detail") or res.get("error")
                return {
                    "error": (
                        f"GitHub repositories could not be retrieved from the backend adapter ({backend_err}). "
                        f"Direct GitHub API access: {direct_res.get('error')}. "
                        "To resolve, configure GITHUB_APP_ID in Spring Boot or set GITHUB_TOKEN in the agent's .env file."
                    ),
                    "backend_error": backend_err,
                    "direct_error": direct_res.get("error"),
                }
        except Exception:
            pass
    return res


@tool
def get_repository(
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
) -> Any:
    """Retrieves detailed information for a single GitHub repository via the Spring Boot GitHub App Adapter.
    Returns repository metadata including id, name, full_name, description, url, visibility, default_branch, programming language,
    open issues count, star count, fork count, creation date, and last updated timestamp.

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}
    Use when asked about details, status, language, branch, stars, issues, or metadata of a specific repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    clean_repo = _resolve_canonical_repo(clean_owner, raw_repo) if clean_owner else _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    res = make_request(f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}")
    if isinstance(res, dict) and "error" in res:
        canonical = _resolve_canonical_repo(clean_owner, clean_repo)
        if canonical and canonical != clean_repo:
            retry_res = make_request(f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(canonical, safe='')}")
            if not (isinstance(retry_res, dict) and "error" in retry_res):
                return retry_res
            clean_repo = canonical
        try:
            from aria_agent.services.github_service import get_github_service
            direct_service = get_github_service()
            direct_res = direct_service.get_repository(clean_repo, org=clean_owner)
            if isinstance(direct_res, dict) and not direct_res.get("error"):
                return direct_res
        except Exception:
            pass
    return res


@tool
def get_owner_repository(
    owner: str,
    repo_name: Optional[str] = None,
    repo: Optional[str] = None,
) -> Any:
    """Retrieves detailed information for a single repository specified by owner and repository name via the Spring Boot GitHub App Adapter.

    Arguments:
    - owner (str): The repository owner (organization or user login, e.g. '<your-org-login>').
    - repo_name (str, optional): The repository name (e.g. '<your-repo-name>').
    - repo (str, optional): Alias for repo_name.

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}
    Use when both owner and repository name are known.
    """
    clean_owner = _clean_repo_identifier(owner)
    clean_repo = _resolve_canonical_repo(clean_owner, repo or repo_name) if clean_owner else _clean_repo_identifier(repo or repo_name)
    if not clean_owner or not clean_repo:
        return {"error": "Both owner and repo_name are required."}

    res = make_request(f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}")
    if isinstance(res, dict) and "error" in res:
        canonical = _resolve_canonical_repo(clean_owner, clean_repo)
        if canonical and canonical != clean_repo:
            retry_res = make_request(f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(canonical, safe='')}")
            if not (isinstance(retry_res, dict) and "error" in retry_res):
                return retry_res
            clean_repo = canonical
        try:
            from aria_agent.services.github_service import get_github_service
            direct_service = get_github_service()
            direct_res = direct_service.get_repository(clean_repo, org=clean_owner)
            if isinstance(direct_res, dict) and not direct_res.get("error"):
                return direct_res
        except Exception:
            pass
    return res


@tool
def list_repository_issues(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
    state: Optional[str] = "open",
    sort: Optional[str] = "updated",
    direction: Optional[str] = "desc",
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Lists issues for a specific repository via the Spring Boot GitHub App Adapter.
    Returns issue details including number, title, state, assignees, labels, author, comments count, creation date, and URL.

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.
    - state (str, optional): Issue state filter ('open', 'closed', 'all'). Default: 'open'.
    - sort (str, optional): Sort field ('created', 'updated', 'comments'). Default: 'updated'.
    - direction (str, optional): Sort direction ('asc', 'desc'). Default: 'desc'.
    - limit (int, optional): Maximum number of issues to return per page.
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/issues
    Use when asked to list, view, find, or search issues, bug reports, or tickets for a specific repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    clean_repo = _resolve_canonical_repo(clean_owner, raw_repo) if clean_owner else _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    params: Dict[str, Any] = {}
    if state and str(state).strip():
        params["state"] = str(state).strip()
    if sort and str(sort).strip():
        params["sort"] = str(sort).strip()
    if direction and str(direction).strip():
        params["direction"] = str(direction).strip()
    if limit is not None:
        try:
            params["limit"] = int(limit)
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    return make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/issues",
        query_params=params if params else None,
    )


@tool
def list_repository_branches(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
    protected: Optional[bool] = None,
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Lists branches for a specific repository via the Spring Boot GitHub App Adapter.
    Returns branch details including branch name, commit SHA, protected status, and protection details.

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.
    - protected (bool, optional): Filter by protected status (True to list only protected branches).
    - limit (int, optional): Maximum number of branches to return per page.
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/branches
    Use when asked to list, view, or check branches, branch protection, or git branches for a specific repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    clean_repo = _resolve_canonical_repo(clean_owner, raw_repo) if clean_owner else _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    params: Dict[str, Any] = {}
    if protected is not None:
        params["protected"] = bool(protected)
    if limit is not None:
        try:
            params["limit"] = int(limit)
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    return make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/branches",
        query_params=params if params else None,
    )


@tool
def list_repository_commits(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
    branch: Optional[str] = None,
    sha: Optional[str] = None,
    author: Optional[str] = None,
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Lists commit history for a specific repository with actual commit messages, SHAs, authors, and dates.
    When 'branch' is omitted, commits are aggregated across all active branches.
    When 'limit' is omitted, all available commits across all branches are returned without artificial caps.
    Employs a 2-tier fallback architecture:
    1. Spring Boot GitHub App Adapter (GET /api/github/repos/{owner}/{repo}/commits)
    2. Direct GitHub REST API (GET /repos/{owner}/{repo}/commits)

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<repository-name>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.
    - branch (str, optional): Specific branch or SHA to inspect (e.g. 'main', 'master', 'feature/platform'). When omitted, commits across all branches are used.
    - sha (str, optional): Optional commit SHA or branch ref to filter commits.
    - author (str, optional): GitHub login or author name to filter by.
    - limit (int, optional): Optional maximum number of commits to return. When omitted, all available commits across all branches are returned.
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Use when asked to view, list, check, inspect, or compare commit messages, recent commits, git history, or changelog for a repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    clean_repo = _resolve_canonical_repo(clean_owner, raw_repo) if clean_owner else _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    params: Dict[str, Any] = {}
    if branch and str(branch).strip():
        params["branch"] = str(branch).strip()
    if sha and str(sha).strip():
        params["sha"] = str(sha).strip()
    if author and str(author).strip():
        params["author"] = str(author).strip()
    parsed_limit: Optional[int] = None
    if limit is not None:
        try:
            val = int(limit)
            if val > 0:
                parsed_limit = val
                params["limit"] = val
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    # Tier 1: Query Spring Boot GitHub App Adapter
    res = make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/commits",
        query_params=params if params else None,
    )
    if isinstance(res, list) and res:
        return res[:parsed_limit] if parsed_limit else res

    # Tier 2: Direct GitHub REST API fallback
    try:
        from aria_agent.services.github_service import get_github_service
        direct_service = get_github_service()
        direct_res = direct_service.list_repository_commits(
            repo_name=clean_repo,
            org=clean_owner,
            limit=parsed_limit,
            branch=branch,
            author=author,
        )
        if isinstance(direct_res, list) and direct_res:
            return direct_res[:parsed_limit] if parsed_limit else direct_res
    except Exception:
        pass

    if isinstance(res, dict) and "error" in res:
        return res

    return []


@tool
def list_repository_languages(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    """Lists programming languages and byte breakdown used in a specific repository via the Spring Boot GitHub App Adapter.
    Returns language names mapped to the number of bytes of code written in that language.

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>' or 'koying/SPMC').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/languages
    Falls back to direct GitHub REST API if the Spring Boot adapter is unavailable.
    If the exact owner/repo combination is not found, automatically searches GitHub for the closest matching repository
    and retries with the discovered owner — or returns a list of candidates if the match is ambiguous.

    Use when asked to list, view, check, or analyze programming languages, language breakdown, tech stack, or lines/bytes of code per language for a specific repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    clean_repo = _resolve_canonical_repo(clean_owner, raw_repo) if clean_owner else _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    res = make_request(f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/languages")
    if isinstance(res, dict) and "error" in res:
        try:
            from aria_agent.services.github_service import get_github_service
            direct_service = get_github_service()
            direct_res = direct_service.list_repository_languages(clean_repo, org=clean_owner)
            if isinstance(direct_res, dict) and not direct_res.get("error"):
                return direct_res
            # If 404, try searching GitHub for the correct owner
            if isinstance(direct_res, dict) and direct_res.get("error"):
                import httpx as _httpx
                search_url = f"https://api.github.com/search/repositories?q={quote(clean_repo, safe='')}+in:name&per_page=5"
                search_headers = {"Accept": "application/vnd.github+json"}
                from aria_agent.config.config import GITHUB_TOKEN
                if GITHUB_TOKEN:
                    search_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
                try:
                    search_r = _httpx.get(search_url, headers=search_headers, timeout=10)
                    if search_r.status_code == 200:
                        items = search_r.json().get("items") or []
                        # Find closest name match (case-insensitive exact repo name)
                        matched = next(
                            (it for it in items if it.get("name", "").lower() == clean_repo.lower()),
                            items[0] if items else None,
                        )
                        if matched:
                            found_owner = matched.get("owner", {}).get("login", "")
                            found_repo = matched.get("name", "")
                            if found_owner and found_repo:
                                retry_res = direct_service.list_repository_languages(found_repo, org=found_owner)
                                if isinstance(retry_res, dict) and not retry_res.get("error"):
                                    return retry_res
                        if items:
                            candidates = ", ".join(f"{it['full_name']}" for it in items[:5])
                            return {
                                "error": (
                                    f"Repository '{clean_owner}/{clean_repo}' not found on GitHub. "
                                    f"Did you mean one of these? {candidates}. "
                                    "Provide the full 'owner/repo' name to retrieve language data."
                                ),
                                "candidates": [it["full_name"] for it in items[:5]],
                            }
                except Exception:
                    pass
                backend_err = res.get("detail") or res.get("error")
                return {
                    "error": (
                        f"Repository '{clean_owner}/{clean_repo}' not found. {backend_err}. "
                        "Please provide the full 'owner/repo' name (e.g., 'koying/SPMC') or configure GITHUB_ORG in the agent's .env file."
                    ),
                    "backend_error": backend_err,
                }
        except Exception:
            pass
    return res


@tool
def list_repository_contributors(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
    anon: Optional[bool] = None,
) -> Any:
    """Lists contributors and their contribution count for a specific repository via the Spring Boot GitHub App Adapter.
    Returns contributor details including login, contributions count, avatar_url, html_url, and type.

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.
    - anon (bool, optional): Include anonymous contributors in results ('true' or 'false').

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/contributors
    Use when asked to list, view, or find contributors, top developers, or commit authors for a specific repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_repo = _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    params: Dict[str, Any] = {}
    if anon is not None:
        params["anon"] = "true" if anon else "false"

    return make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/contributors",
        query_params=params if params else None,
    )


@tool
def list_contributors_for_each_repository(
    org: Optional[str] = None,
) -> Any:
    """Lists contributors grouped by repository for an organization or installation via the Spring Boot GitHub App Adapter.
    Returns a dictionary mapping each repository name to its list of contributors with contribution counts.

    Arguments:
    - org (str, optional): Target GitHub organization login (e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.

    Maps to Spring Boot: GET /api/github/orgs/{org}/repos/contributors (or GET /api/github/repos/contributors)
    Use when asked to list contributors for each repository, all contributors across repositories, or repository-grouped contributors.
    """
    clean_org = _clean_repo_identifier(org) if org and str(org).strip() else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if clean_org:
        return make_request(f"/api/github/orgs/{quote(clean_org, safe='')}/repos/contributors")
    return make_request("/api/github/repos/contributors")




@tool
def list_branch_commits(
    branch: str,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    """Lists commits (including commit messages, author, timestamp, and SHA) for a specific branch of a repository via the Spring Boot GitHub App Adapter.

    Arguments:
    - branch (str): The specific branch name (e.g. 'main', 'feature/login').
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/branches/{branch}/commits
    Use when asked to list, view, or check commits specifically for a designated branch.
    """
    clean_branch = str(branch).strip() if branch else ""
    if not clean_branch:
        return {"error": "Branch name is required."}

    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_repo = _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    return make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/branches/{quote(clean_branch, safe='')}/commits"
    )


@tool
def list_repository_commit_messages(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
    branch: Optional[str] = None,
    sha: Optional[str] = None,
) -> Any:
    """Lists commit messages for a specific repository via the Spring Boot GitHub App Adapter.
    Can optionally filter by branch or commit SHA.

    Arguments:
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.
    - branch (str, optional): Optional branch name to filter commit messages (e.g. 'main', 'develop').
    - sha (str, optional): Optional commit SHA or branch ref to filter commit messages.

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/commit-messages
    Use when asked to list, show, or summarize commit messages for a repository.
    """
    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_repo = _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    params: Dict[str, Any] = {}
    if branch and str(branch).strip():
        params["branch"] = str(branch).strip()
    if sha and str(sha).strip():
        params["sha"] = str(sha).strip()

    return make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/commit-messages",
        query_params=params if params else None,
    )


@tool
def list_branch_commit_messages(
    branch: str,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    repo_name: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    """Lists commit messages for a specific branch of a repository via the Spring Boot GitHub App Adapter.

    Arguments:
    - branch (str): The specific branch name (e.g. 'main', 'feature/login').
    - owner (str, optional): The repository owner (organization or user login, e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG.
    - repo (str, optional): The repository name (e.g. '<your-repo-name>' or '<your-org>/<your-repo>').
    - repo_name (str, optional): Alias for repo.
    - org (str, optional): Alias for owner.

    Maps to Spring Boot: GET /api/github/repos/{owner}/{repo}/branches/{branch}/commit-messages
    Use when asked to list, view, or check commit messages specifically for a branch.
    """
    clean_branch = str(branch).strip() if branch else ""
    if not clean_branch:
        return {"error": "Branch name is required."}

    raw_repo = (repo or repo_name or "").strip()
    raw_owner = (owner or org or "").strip()

    if not raw_repo and raw_owner and "/" in raw_owner:
        parts = raw_owner.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]
    elif "/" in raw_repo:
        parts = raw_repo.split("/", 1)
        raw_owner, raw_repo = parts[0], parts[1]

    clean_repo = _clean_repo_identifier(raw_repo)
    if not clean_repo:
        return {"error": "Repository name cannot be empty."}

    clean_owner = _clean_repo_identifier(raw_owner) if raw_owner else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_owner:
        return {"error": "Repository owner or organization is required. Provide 'owner' or configure GITHUB_ORG."}

    return make_request(
        f"/api/github/repos/{quote(clean_owner, safe='')}/{quote(clean_repo, safe='')}/branches/{quote(clean_branch, safe='')}/commit-messages"
    )


@tool
def list_org_members(
    org: Optional[str] = None,
    filter: Optional[str] = "all",
    role: Optional[str] = "all",
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Lists organization members for a specified GitHub organization via the Spring Boot GitHub App Adapter.
    Returns member details including login, id, avatar_url, html_url, role, and type.

    Arguments:
    - org (str, optional): Target GitHub organization login specified in the URL path (e.g. '<your-org-login>'). Defaults to configured GITHUB_ORG if omitted.
    - filter (str, optional): Filter members by 2FA status ('2fa_disabled', 'all'). Default: 'all'.
    - role (str, optional): Filter by member role ('all', 'admin', 'member'). Default: 'all'.
    - limit (int, optional): Maximum number of members to return per page.
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Maps to Spring Boot: GET /api/github/orgs/{org}/members
    Use when asked to list, show, or find members of a specific GitHub organization.
    """
    clean_org = _clean_repo_identifier(org) if org and str(org).strip() else (GITHUB_ORG.strip() if GITHUB_ORG else "")
    if not clean_org:
        return {"error": "Organization name is required."}

    params: Dict[str, Any] = {}
    if filter and str(filter).strip():
        params["filter"] = str(filter).strip()
    if role and str(role).strip():
        params["role"] = str(role).strip()
    if limit is not None:
        try:
            params["limit"] = int(limit)
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    return make_request(f"/api/github/orgs/{quote(clean_org, safe='')}/members", query_params=params if params else None)


@tool
def list_members(
    org: Optional[str] = None,
    filter: Optional[str] = "all",
    role: Optional[str] = "all",
    limit: OptionalReadLimit = None,
    page: Optional[int] = 1,
) -> Any:
    """Lists organization members via the Spring Boot GitHub App Adapter.
    Returns member details including login, id, avatar_url, html_url, role, and type.

    Arguments:
    - org (str, optional): Target GitHub organization login. Defaults to configured GITHUB_ORG.
    - filter (str, optional): Filter members by 2FA status ('2fa_disabled', 'all'). Default: 'all'.
    - role (str, optional): Filter by member role ('all', 'admin', 'member'). Default: 'all'.
    - limit (int, optional): Maximum number of members to return per page.
    - page (int, optional): Page number for pagination (1-based, default: 1).

    Maps to Spring Boot: GET /api/github/members
    Use when asked to list, show, or find members or collaborators of the organization on GitHub.
    """
    params: Dict[str, Any] = {}
    target_org = org.strip() if org and str(org).strip() else (GITHUB_ORG.strip() if GITHUB_ORG else None)
    if target_org:
        params["org"] = target_org
    if filter and str(filter).strip():
        params["filter"] = str(filter).strip()
    if role and str(role).strip():
        params["role"] = str(role).strip()
    if limit is not None:
        try:
            params["limit"] = int(limit)
        except (ValueError, TypeError):
            pass
    if page is not None:
        try:
            p_val = int(page)
            if p_val > 1:
                params["page"] = p_val
        except (ValueError, TypeError):
            pass

    return make_request("/api/github/members", query_params=params if params else None)


# Domain metadata for vector similarity routing
for t, ep in [
    (list_repositories, "/api/github/repos"),
    (list_org_repositories, "/api/github/orgs/{org}/repos"),
    (get_repository, "/api/github/repos/{owner}/{repo}"),
    (get_owner_repository, "/api/github/repos/{owner}/{repo}"),
    (list_repository_issues, "/api/github/repos/{owner}/{repo}/issues"),
    (list_repository_branches, "/api/github/repos/{owner}/{repo}/branches"),
    (list_repository_commits, "/api/github/repos/{owner}/{repo}/commits"),
    (list_repository_languages, "/api/github/repos/{owner}/{repo}/languages"),
    (list_repository_contributors, "/api/github/repos/{owner}/{repo}/contributors"),
    (list_contributors_for_each_repository, "/api/github/repos/contributors"),
    (list_repository_commits, "/api/github/repos/{owner}/{repo}/commits"),
    (list_branch_commits, "/api/github/repos/{owner}/{repo}/branches/{branch}/commits"),
    (list_repository_commit_messages, "/api/github/repos/{owner}/{repo}/commit-messages"),
    (list_branch_commit_messages, "/api/github/repos/{owner}/{repo}/branches/{branch}/commit-messages"),
    (list_org_members, "/api/github/orgs/{org}/members"),
    (list_members, "/api/github/members"),
]:
    t.metadata = {
        "domain": "REPOSITORIES",
        "path": ep,
        "tags": ["GitHub Organization", "GitHub Repositories", "REPOSITORIES"],
    }


# Backward-compatible and camelCase aliases
listRepositories = list_repositories
listOrgRepositories = list_org_repositories
getRepository = get_repository
getOwnerRepository = get_owner_repository
getRepositories = list_repositories
listRepositoryIssues = list_repository_issues
getRepositoryIssues = list_repository_issues
listRepositoryBranches = list_repository_branches
getRepositoryBranches = list_repository_branches
listRepositoryCommits = list_repository_commits
getRepositoryCommits = list_repository_commits
get_repository_commits = list_repository_commits
listRepositoryLanguages = list_repository_languages
getRepositoryLanguages = list_repository_languages
get_repository_languages = list_repository_languages
listRepositoryContributors = list_repository_contributors
getRepositoryContributors = list_repository_contributors
get_repository_contributors = list_repository_contributors
listContributors = list_repository_contributors
listContributorsForEachRepository = list_contributors_for_each_repository
getContributorsForEachRepository = list_contributors_for_each_repository
list_contributors_by_repository = list_contributors_for_each_repository
get_contributors_for_each_repository = list_contributors_for_each_repository
listRepositoryCommits = list_repository_commits
getRepositoryCommits = list_repository_commits
get_repository_commits = list_repository_commits
listCommits = list_repository_commits
listBranchCommits = list_branch_commits
getBranchCommits = list_branch_commits
get_branch_commits = list_branch_commits
listRepositoryCommitMessages = list_repository_commit_messages
get_repository_commit_messages = list_repository_commit_messages
listCommitMessages = list_repository_commit_messages
getCommitMessages = list_repository_commit_messages
listBranchCommitMessages = list_branch_commit_messages
getBranchCommitMessages = list_branch_commit_messages
get_branch_commit_messages = list_branch_commit_messages
listOrgMembers = list_org_members
getOrgMembers = list_org_members
listMembers = list_members
getMembers = list_members
listOrganizationMembers = list_members
list_organization_members = list_members

__all__ = [
    "list_repositories",
    "list_org_repositories",
    "get_repository",
    "get_owner_repository",
    "list_repository_issues",
    "list_repository_branches",
    "list_repository_commits",
    "list_repository_languages",
    "get_repository_languages",
    "list_repository_contributors",
    "get_repository_contributors",
    "list_contributors_for_each_repository",
    "list_contributors_by_repository",
    "get_contributors_for_each_repository",
    "list_repository_commits",
    "get_repository_commits",
    "list_branch_commits",
    "get_branch_commits",
    "list_repository_commit_messages",
    "get_repository_commit_messages",
    "list_branch_commit_messages",
    "get_branch_commit_messages",
    "list_org_members",
    "list_members",
    "listRepositories",
    "listOrgRepositories",
    "getRepository",
    "getOwnerRepository",
    "getRepositories",
    "listRepositoryIssues",
    "getRepositoryIssues",
    "listRepositoryBranches",
    "getRepositoryBranches",
    "listRepositoryCommits",
    "getRepositoryCommits",
    "get_repository_commits",
    "listRepositoryLanguages",
    "getRepositoryLanguages",
    "listRepositoryContributors",
    "getRepositoryContributors",
    "listContributors",
    "listContributorsForEachRepository",
    "getContributorsForEachRepository",
    "listRepositoryCommits",
    "getRepositoryCommits",
    "listCommits",
    "listBranchCommits",
    "getBranchCommits",
    "listRepositoryCommitMessages",
    "listCommitMessages",
    "getCommitMessages",
    "listBranchCommitMessages",
    "getBranchCommitMessages",
    "listOrgMembers",
    "getOrgMembers",
    "listMembers",
    "getMembers",
    "listOrganizationMembers",
    "list_organization_members",
]
