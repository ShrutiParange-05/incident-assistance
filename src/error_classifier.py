"""
Error classification engine (the "Incident Analyzer" box in the
architecture diagram: Error Type + Root Cause).

Deliberately rule-based rather than another LLM call: classification
needs to be fast, deterministic, and auditable — you want the exact
same input to always land in the exact same bucket. The GenAI layer
is reserved for the part that actually benefits from natural-language
reasoning: turning a bucket into concrete troubleshooting steps.

Extend `RULES` to grow the taxonomy without touching any other file.
"""
from dataclasses import dataclass


@dataclass
class Classification:
    error_type: str
    probable_cause: str
    severity: str  # "Low" | "Medium" | "High" | "Critical"


# Ordered list of (keywords, http_codes, Classification). First match wins,
# so put more specific rules before generic ones.
RULES: list[tuple[list[str], list[int], Classification]] = [
    (
        ["connection pool", "pool exhaust", "too many connections"],
        [500, 503],
        Classification(
            error_type="Database Connectivity",
            probable_cause="Connection pool exhaustion",
            severity="High",
        ),
    ),
    (
        ["timeout", "timed out"],
        [500, 502, 503, 504],
        Classification(
            error_type="Database Connectivity",
            probable_cause="Database connection timeout (slow query, network latency, or DB overload)",
            severity="High",
        ),
    ),
    (
        ["deadlock"],
        [500],
        Classification(
            error_type="Database Concurrency",
            probable_cause="Transaction deadlock from concurrent writes",
            severity="High",
        ),
    ),
    (
        ["unique constraint", "duplicate key", "integrity"],
        [400, 409, 500],
        Classification(
            error_type="Database Integrity",
            probable_cause="Constraint violation from duplicate or invalid data",
            severity="Medium",
        ),
    ),
    (
        ["auth", "token", "unauthorized", "forbidden", "permission denied"],
        [401, 403],
        Classification(
            error_type="Authentication/Authorization",
            probable_cause="Expired, missing, or invalid credentials/token",
            severity="Medium",
        ),
    ),
    (
        ["rate limit", "too many requests", "throttle"],
        [429],
        Classification(
            error_type="Rate Limiting",
            probable_cause="Client exceeded allowed request rate, or upstream quota reached",
            severity="Low",
        ),
    ),
    (
        ["validation", "invalid input", "bad request", "missing field", "schema"],
        [400, 422],
        Classification(
            error_type="Input Validation",
            probable_cause="Client sent malformed or incomplete request payload",
            severity="Low",
        ),
    ),
    (
        ["not found", "does not exist", "no such"],
        [404],
        Classification(
            error_type="Resource Not Found",
            probable_cause="Requested resource does not exist or was already deleted",
            severity="Low",
        ),
    ),
    (
        ["memory", "oom", "out of memory"],
        [500, 503],
        Classification(
            error_type="Resource Exhaustion",
            probable_cause="Process exceeded available memory",
            severity="Critical",
        ),
    ),
    (
        ["disk", "no space left"],
        [500, 507],
        Classification(
            error_type="Resource Exhaustion",
            probable_cause="Host or volume ran out of disk space",
            severity="Critical",
        ),
    ),
    (
        ["dns", "could not resolve", "name resolution"],
        [502, 503, 504],
        Classification(
            error_type="Network/DNS",
            probable_cause="Downstream service hostname failed to resolve",
            severity="High",
        ),
    ),
    (
        ["connection refused", "econnrefused"],
        [502, 503],
        Classification(
            error_type="Downstream Service Unavailable",
            probable_cause="Dependent service is down or unreachable",
            severity="High",
        ),
    ),
    (
        ["null", "nonetype", "attributeerror", "keyerror"],
        [500],
        Classification(
            error_type="Application Bug",
            probable_cause="Unhandled null reference or missing key in application code",
            severity="Medium",
        ),
    ),
]

DEFAULT_CLASSIFICATION = Classification(
    error_type="Unclassified",
    probable_cause="No matching rule — message did not contain any recognized error signature",
    severity="Medium",
)


def classify(message: str, error_code: int) -> Classification:
    """Classify an incident from its free-text message + HTTP/status code."""
    text = message.lower()

    for keywords, codes, classification in RULES:
        keyword_hit = any(kw in text for kw in keywords)
        code_hit = error_code in codes
        if keyword_hit and (not codes or code_hit):
            return classification

    # Fall back to a generic bucket by status-code family if no keyword matched.
    if error_code >= 500:
        return Classification(
            error_type="Server Error",
            probable_cause="Unhandled exception on the server; no specific signature matched",
            severity="High",
        )
    if error_code >= 400:
        return Classification(
            error_type="Client Error",
            probable_cause="Request rejected by the server; no specific signature matched",
            severity="Low",
        )

    return DEFAULT_CLASSIFICATION
