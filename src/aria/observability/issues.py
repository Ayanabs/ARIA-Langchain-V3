"""Problems a request can run into, described for the people analysing it.

Each issue has a stable code, a severity, a title, an explanation of what happened and a hint on
what to check. The specifics of one occurrence go in `detail`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

ERROR = "error"
WARNING = "warning"
INFO = "info"


@dataclass(frozen=True)
class IssueKind:
    severity: str
    title: str
    explanation: str
    hint: str


KINDS: dict[str, IssueKind] = {
    "model_timeout": IssueKind(
        ERROR,
        "Model call timed out",
        "The model host did not answer within the configured timeout, so this step produced nothing.",
        "Check the model host's load and network path; raise timeout_seconds in the model profile only "
        "if replies are known to be slow.",
    ),
    "model_unreachable": IssueKind(
        ERROR,
        "Model host unreachable",
        "ARIA could not open a connection to the model host after its retry budget.",
        "Check that the model host is running and reachable from ARIA (address in .env).",
    ),
    "model_provider_error": IssueKind(
        ERROR,
        "Model host returned an error",
        "The model host answered with an HTTP error instead of a reply.",
        "Look at the model host's own logs for the request at this time.",
    ),
    "context_capacity": IssueKind(
        ERROR,
        "Prompt too large for the model",
        "The prompt would exceed the model's input budget, so it was not sent rather than being silently "
        "cut short by the host.",
        "Fewer tools per call or less evidence keeps prompts within budget; check input_budget_tokens.",
    ),
    "invalid_output": IssueKind(
        ERROR,
        "Model output was not valid",
        "The model's reply did not match the required structure.",
        "Check that the model supports structured output and that structured_output is set correctly.",
    ),
    "output_limit": IssueKind(
        ERROR,
        "Model reply was cut off",
        "The model reached its output token limit before finishing.",
        "Raise max_output_tokens in the model profile, or ask for shorter answers in the prompts.",
    ),
    "no_tools_shortlisted": IssueKind(
        WARNING,
        "No tool matched the question",
        "The tool search found no tool related to the question's words, so no data could be retrieved.",
        "If a tool should have matched, improve its description; semantic search will also help once "
        "the embedding service is reachable.",
    ),
    "answered_without_tools": IssueKind(
        INFO,
        "Answered without retrieving data",
        "The model judged that none of the shortlisted tools fits the question, so it replied "
        "conversationally.",
        "If the question needed records, check that the right tool was in the shortlist below.",
    ),
    "argument_rejected": IssueKind(
        WARNING,
        "An argument was rejected",
        "A value the model proposed was not used, because it could not be traced to the user's words, an "
        "earlier result or the caller's identity, or did not match the parameter's type.",
        "This is a safety check working; if the value was right, the user may need to state it explicitly.",
    ),
    "missing_key": IssueKind(
        WARNING,
        "A needed identifier was not available",
        "The chosen tool needs an identifier that the question did not give and no shortlisted lookup "
        "could find with the words the user wrote.",
        "Check that a lookup tool produces this key and that the model filled in its arguments.",
    ),
    "dependency_cycle": IssueKind(
        ERROR,
        "Tools depend on each other in a loop",
        "Each tool in the chain needs a key that only the next one can produce.",
        "Declare another producer for one of the keys, or remove the loop in the key declarations.",
    ),
    "chain_too_deep": IssueKind(
        WARNING,
        "Lookup chain too long",
        "Finding the needed identifier would take more lookups than max_chain_depth allows.",
        "Raise max_chain_depth if such chains are expected.",
    ),
    "fan_out_limit": IssueKind(
        WARNING,
        "Too many records to look up one by one",
        "An earlier step selected more subjects than max_fan_out calls allow.",
        "Ask about fewer subjects, or raise max_fan_out if this is expected.",
    ),
    "invented_key": IssueKind(
        WARNING,
        "Identifier not from a trusted source",
        "The model supplied an identifier for a step that must take it from an earlier result.",
        "This is a safety check working; no backend call was made.",
    ),
    "backend_error": IssueKind(
        ERROR,
        "Backend call failed",
        "A backend operation returned an error or could not be reached.",
        "The status code tells which: 401/403 is the caller's access, 404 a missing record, 5xx a backend "
        "fault to look up in the backend log.",
    ),
    "no_records": IssueKind(
        INFO,
        "No matching records",
        "A lookup returned no records for the values given, so the chain stopped there.",
        "Check the spelling of names or values, and that the caller is allowed to see these records.",
    ),
    "ambiguous_subject": IssueKind(
        INFO,
        "Several records matched",
        "More than one record matched, so ARIA asked the user which one they meant instead of guessing.",
        "Nothing to fix; the user's answer resolves it.",
    ),
    "evidence_truncated": IssueKind(
        INFO,
        "Only part of the data was shown to the model",
        "More records were retrieved than fit the synthesis budget; the model was told the total and "
        "that it sees only some of them.",
        "The full rows stay in code; totals and charts are computed from all of them.",
    ),
    "catalog_unavailable": IssueKind(
        ERROR,
        "Tool catalog not loaded",
        "The tool catalog could not be built from the backend contract, so no tools were available.",
        "Check that the backend is reachable and run `python -m aria catalog` for the reasons.",
    ),
    "unexpected_error": IssueKind(
        ERROR,
        "Unexpected error",
        "The request failed in a way ARIA does not classify.",
        "Look up the trace ID in ARIA's log for the full error.",
    ),
}


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    title: str
    explanation: str
    hint: str
    stage: str
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def issue(code: str, stage: str, detail: str = "") -> Issue:
    kind = KINDS.get(code, KINDS["unexpected_error"])
    return Issue(code, kind.severity, kind.title, kind.explanation, kind.hint, stage, detail)
