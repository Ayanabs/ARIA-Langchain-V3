"""GitHub Projects API Tools for ARIA LangChain Agent (Spring Boot Adapter Integration).

Provides read-only LangChain tools connecting to the Spring Boot GitHub Adapter Service:
- list_projects: Enumerates GitHub Projects via GET /api/projects
- get_project_issues: Retrieves issues / issue status via GET /api/projects/{id}/issues
- get_project_sprint: Retrieves sprint progress via GET /api/projects/{id}/sprint
- get_team_workload: Retrieves team workload distribution via GET /api/team/{id}/workload
"""

import os
from typing import Any, Optional
from aria_agent.schemas.retrieval import ReadLimit
from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id


def _get_default_project_number(project_number: Optional[Any] = None) -> str:
    """Resolves default project number or string identifier."""
    if project_number is not None and str(project_number).strip():
        return clean_id(str(project_number).strip())
    env_proj = os.getenv("GITHUB_PROJECT_NUMBER", "").strip()
    if env_proj:
        return clean_id(env_proj)
    return "1"


@tool
def list_projects(org: Optional[str] = None, limit: ReadLimit = 10) -> Any:
    """Lists GitHub Projects (Projects v2 and classic) for an organization or account via Spring Boot GitHub Adapter.
    Returns project number, title, short description, item count, URL, and open/closed state.

    Arguments:
    - org (str, optional): Target GitHub organization or account login. Defaults to GITHUB_ORG environment variable.
    - limit (int, optional): Maximum number of projects to return (1-100, default: 10).

    Maps to Spring Boot: GET /api/projects (and /projects)
    Use when asked to show, list, or find GitHub projects or roadmaps for an organization.
    """
    params = {}
    if org and str(org).strip():
        params["org"] = str(org).strip()
    if limit:
        params["limit"] = str(limit)

    res = make_request("/api/projects", query_params=params if params else None)
    if isinstance(res, dict) and "error" in res:
        try:
            from aria_agent.services.github_service import get_github_service
            direct_service = get_github_service()
            direct_res = direct_service.list_projects(org=org, limit=limit)
            if isinstance(direct_res, list) and len(direct_res) > 0:
                return direct_res
            if isinstance(direct_res, dict) and direct_res.get("error"):
                backend_err = res.get("detail") or res.get("error")
                return {
                    "error": (
                        f"GitHub projects could not be retrieved from backend adapter ({backend_err}). "
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
def get_project_issues(
    project_number: Optional[int] = None,
    issue_number: Optional[int] = None,
    repo: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    """Retrieves issues, board status, column, assignees, and sprint details for a GitHub project or specific issue via Spring Boot GitHub Adapter.

    Arguments:
    - project_number (int, optional): The GitHub Project number. Defaults to GITHUB_PROJECT_NUMBER.
    - issue_number (int, optional): Specific GitHub issue number (e.g. 42) to filter.
    - repo (str, optional): Target repository name (e.g. 'aria-core' or 'org/aria-core').
    - org (str, optional): Target GitHub organization.

    Maps to Spring Boot: GET /api/projects/{id}/issues (and /projects/{id}/issues)
    Returns list of issues or specific issue details including title, state, project_status, assignees, labels, sprint, and URL.
    """
    proj_id = _get_default_project_number(project_number)
    params = {}
    if issue_number is not None:
        params["issue_number"] = str(issue_number)
    if repo and str(repo).strip():
        params["repo"] = str(repo).strip()
    if org and str(org).strip():
        params["org"] = str(org).strip()

    return make_request(f"/api/projects/{proj_id}/issues", query_params=params if params else None)


@tool
def get_issue_status(
    issue_number: int,
    project_number: Optional[int] = None,
    repo: Optional[str] = None,
) -> Any:
    """Retrieves the current status, project board column, assignees, sprint/iteration, and details of a GitHub issue via Spring Boot GitHub Adapter.

    Arguments:
    - issue_number (int): The GitHub issue number (e.g. 42).
    - project_number (int, optional): The GitHub Project number. Defaults to GITHUB_PROJECT_NUMBER environment variable.
    - repo (str, optional): Target repository name (e.g. 'aria-core' or 'org/aria-core') if searching repository directly.

    Maps to Spring Boot: GET /api/projects/{id}/issues?issue_number={issue_number}
    Returns issue title, state (OPEN/CLOSED), project_status (e.g. 'Todo', 'In Progress', 'Done'),
    assignees, sprint, labels, milestone, and URL.
    Use when asked about the status, progress, or state of a specific issue.
    """
    proj_id = _get_default_project_number(project_number)
    params = {"issue_number": str(issue_number)}
    if repo and str(repo).strip():
        params["repo"] = str(repo).strip()

    return make_request(f"/api/projects/{proj_id}/issues", query_params=params)


@tool
def get_project_sprint(
    project_number: Optional[int] = None,
    sprint_name: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    """Calculates sprint or iteration progress for a GitHub project, including completion percentage,
    count of completed, in-progress, and todo issues, status breakdown, and issue details via Spring Boot GitHub Adapter.

    Arguments:
    - project_number (int, optional): The GitHub Project number. Defaults to GITHUB_PROJECT_NUMBER environment variable.
    - sprint_name (str, optional): Name or title of the sprint/iteration (e.g. 'Sprint 3' or 'Iteration 14').
      If omitted, automatically detects and reports on the currently active sprint.
    - org (str, optional): Target GitHub organization.

    Maps to Spring Boot: GET /api/projects/{id}/sprint (and /projects/{id}/sprint)
    Returns total issues, completed issues, in progress, todo, completion percentage, and item summaries.
    Use when asked about sprint progress, sprint burndown, iteration status, or completion rate.
    """
    proj_id = _get_default_project_number(project_number)
    params = {}
    if sprint_name and str(sprint_name).strip():
        params["sprint_name"] = str(sprint_name).strip()
    if org and str(org).strip():
        params["org"] = str(org).strip()

    return make_request(f"/api/projects/{proj_id}/sprint", query_params=params if params else None)


@tool
def get_sprint_progress(
    sprint_name: Optional[str] = None,
    project_number: Optional[int] = None,
) -> Any:
    """Calculates sprint or iteration progress for a GitHub project, including completion percentage,
    count of completed, in-progress, and todo issues, status breakdown, and issue details via Spring Boot GitHub Adapter.

    Arguments:
    - sprint_name (str, optional): Name or title of the sprint/iteration (e.g. 'Sprint 3' or 'Iteration 14').
      If omitted, automatically detects and reports on the currently active sprint.
    - project_number (int, optional): The GitHub Project number. Defaults to GITHUB_PROJECT_NUMBER environment variable.

    Maps to Spring Boot: GET /api/projects/{id}/sprint
    Returns total issues, completed issues, in progress, todo, completion percentage, and item summaries.
    """
    proj_id = _get_default_project_number(project_number)
    params = {}
    if sprint_name and str(sprint_name).strip():
        params["sprint_name"] = str(sprint_name).strip()

    return make_request(f"/api/projects/{proj_id}/sprint", query_params=params if params else None)


@tool
def get_team_workload(
    project_number: Optional[int] = None,
    sprint_name: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    """Calculates team workload distribution across members in a GitHub Project, showing assigned issues,
    status breakdown (in-progress, completed, todo), and unassigned task counts via Spring Boot GitHub Adapter.

    Arguments:
    - project_number (int, optional): The GitHub Project number or team ID. Defaults to GITHUB_PROJECT_NUMBER.
    - sprint_name (str, optional): Optional filter for a specific sprint/iteration. If omitted, aggregates across all project items.
    - org (str, optional): Target GitHub organization.

    Maps to Spring Boot: GET /api/team/{id}/workload (and /team/{id}/workload)
    Returns workload per team member (assigned tasks, in-progress, completed, todo) and unassigned task count.
    Use when asked about team workload, who is working on what, developer allocation, or task distribution.
    """
    proj_id = _get_default_project_number(project_number)
    params = {}
    if sprint_name and str(sprint_name).strip():
        params["sprint_name"] = str(sprint_name).strip()
    if org and str(org).strip():
        params["org"] = str(org).strip()

    return make_request(f"/api/team/{proj_id}/workload", query_params=params if params else None)


from aria_agent.tools.github_repositories import (
    list_repositories,
    list_org_repositories,
    get_repository,
    get_owner_repository,
    list_repository_issues,
    list_repository_branches,
    list_repository_commits,
    list_repository_languages,
    get_repository_languages,
    list_repository_contributors,
    get_repository_contributors,
    list_contributors_for_each_repository,
    list_contributors_by_repository,
    get_contributors_for_each_repository,
    list_repository_commits,
    get_repository_commits,
    list_branch_commits,
    get_branch_commits,
    list_repository_commit_messages,
    get_repository_commit_messages,
    list_branch_commit_messages,
    get_branch_commit_messages,
    list_org_members,
    list_members,
    listRepositories,
    listOrgRepositories,
    getRepository,
    getOwnerRepository,
    getRepositories,
    listRepositoryIssues,
    getRepositoryIssues,
    listRepositoryBranches,
    getRepositoryBranches,
    listRepositoryCommits,
    getRepositoryCommits,
    get_repository_commits,
    listRepositoryLanguages,
    getRepositoryLanguages,
    listRepositoryContributors,
    getRepositoryContributors,
    listContributors,
    listContributorsForEachRepository,
    listRepositoryCommits,
    getRepositoryCommits,
    listCommits,
    listBranchCommits,
    getBranchCommits,
    listRepositoryCommitMessages,
    listCommitMessages,
    getCommitMessages,
    listBranchCommitMessages,
    getBranchCommitMessages,
    listOrgMembers,
    getOrgMembers,
    listMembers,
    getMembers,
    listOrganizationMembers,
    list_organization_members,
)


# Backward-compatible camelCase aliases
listProjects = list_projects
getProjectIssues = get_project_issues
getIssueStatus = get_issue_status
getProjectSprint = get_project_sprint
getSprintProgress = get_sprint_progress
getTeamWorkload = get_team_workload
listRepositories = list_repositories
getRepositories = list_repositories
getRepository = get_repository

__all__ = [
    "list_projects",
    "get_project_issues",
    "get_issue_status",
    "get_project_sprint",
    "get_sprint_progress",
    "get_team_workload",
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
    "listProjects",
    "getProjectIssues",
    "getIssueStatus",
    "getProjectSprint",
    "getSprintProgress",
    "getTeamWorkload",
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
