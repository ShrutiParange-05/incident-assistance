"""
The "documentation" the RAG layer retrieves from.

In a real system this would be your Confluence/Notion runbooks,
postmortems, and internal wiki, ingested via a loader + embedding
pipeline. For this project it's a small in-repo runbook set so the
whole thing runs with zero external dependencies — swap
`DOCUMENTS` for a loader over your own docs folder and nothing else
in the RAG pipeline needs to change.
"""

DOCUMENTS: list[dict] = [
    {
        "id": "runbook-db-pool",
        "title": "Database Connection Pool Exhaustion",
        "tags": ["Database Connectivity", "Database Concurrency"],
        "content": (
            "Connection pool exhaustion happens when the number of concurrent "
            "DB sessions exceeds the pool's max_overflow + pool_size. Check "
            "pg_stat_activity for idle-in-transaction sessions, verify the "
            "app closes sessions/connections in a finally block, confirm the "
            "pool size matches expected concurrent load, and check for a "
            "connection leak in recently deployed code. Short-term mitigation: "
            "restart the affected pods to release stuck connections and "
            "temporarily raise pool_size."
        ),
    },
    {
        "id": "runbook-db-timeout",
        "title": "Database Connection Timeout",
        "tags": ["Database Connectivity"],
        "content": (
            "Timeouts usually mean either the DB is overloaded (check CPU, "
            "active queries, and locks on the DB host), the network path "
            "between app and DB has latency/packet loss, or a slow query is "
            "blocking the connection. Run EXPLAIN ANALYZE on recent slow "
            "queries, check for missing indexes, and confirm the DB host's "
            "resource metrics in the monitoring dashboard."
        ),
    },
    {
        "id": "runbook-auth",
        "title": "Authentication and Authorization Failures",
        "tags": ["Authentication/Authorization"],
        "content": (
            "401/403 spikes are usually caused by expired API keys/JWTs, "
            "clock skew between services breaking token validation, or an "
            "IAM/permission change. Check the identity provider's status "
            "page, verify token expiry configuration, and confirm the "
            "service account's role bindings were not recently modified."
        ),
    },
    {
        "id": "runbook-rate-limit",
        "title": "Rate Limiting / 429s",
        "tags": ["Rate Limiting"],
        "content": (
            "429s mean a client (or your service acting as a client to a "
            "downstream API) exceeded quota. Check whether a specific caller "
            "is retrying aggressively without backoff, verify your rate "
            "limiter's window/threshold config, and consider adding "
            "exponential backoff with jitter on the client side."
        ),
    },
    {
        "id": "runbook-downstream",
        "title": "Downstream Service Unavailable",
        "tags": ["Downstream Service Unavailable", "Network/DNS"],
        "content": (
            "Connection-refused or DNS failures to a dependency usually mean "
            "the downstream service is down, a network policy/security group "
            "changed, or its DNS record is misconfigured. Check the "
            "downstream service's own health dashboard first, then verify "
            "service discovery / DNS resolution from inside the failing "
            "pod, and check for recent network policy changes."
        ),
    },
    {
        "id": "runbook-resource-exhaustion",
        "title": "Memory / Disk Exhaustion",
        "tags": ["Resource Exhaustion"],
        "content": (
            "OOM kills or disk-full errors need immediate remediation: "
            "restart the affected instance to restore service, then "
            "investigate. For memory, check for unbounded caches, large "
            "response payloads being buffered in memory, or a recent memory "
            "leak in a new deploy. For disk, check log rotation config and "
            "any temp file accumulation."
        ),
    },
    {
        "id": "runbook-validation",
        "title": "Input Validation Errors",
        "tags": ["Input Validation"],
        "content": (
            "400/422 spikes usually trace back to a client sending an "
            "outdated payload shape after an API contract change, or a "
            "frontend deploy that got out of sync with the backend schema. "
            "Check recent API version changes and confirm client/server "
            "contract versions match."
        ),
    },
    {
        "id": "runbook-application-bug",
        "title": "Unhandled Application Exceptions",
        "tags": ["Application Bug"],
        "content": (
            "NoneType/AttributeError/KeyError in production usually means an "
            "edge case (missing optional field, empty list, None from an "
            "external API) wasn't handled. Reproduce with the exact input "
            "from the error log, add a regression test for that input, and "
            "add explicit null/empty checks around the failing code path."
        ),
    },
]


def all_documents() -> list[dict]:
    return DOCUMENTS
