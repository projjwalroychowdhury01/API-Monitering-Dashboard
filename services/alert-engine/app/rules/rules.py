# rules/rules.py
# Named threshold constants for alert evaluation.
# All magic numbers belong here — never inline in logic.
#
# Two-tier severity model:
#   WARNING  — metric is degraded; investigate soon.
#   CRITICAL — metric is severely degraded; act immediately.

# ---------------------------------------------------------------------------
# Latency: p95 response time in milliseconds
# ---------------------------------------------------------------------------

LATENCY_P95_WARNING: float = 500.0   # > 500 ms → WARNING
LATENCY_P95_CRITICAL: float = 1000.0  # > 1 000 ms → CRITICAL

# ---------------------------------------------------------------------------
# Error rate: fraction of requests that returned an error (0.0 – 1.0)
# ---------------------------------------------------------------------------

ERROR_RATE_WARNING: float = 0.05   # > 5 %  → WARNING
ERROR_RATE_CRITICAL: float = 0.15  # > 15 % → CRITICAL
