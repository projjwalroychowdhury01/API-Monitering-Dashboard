# rules/rules.py
# Named threshold constants for alert evaluation.
# All magic numbers belong here — never inline in logic.

# Latency: p95 response time in milliseconds above which an alert fires.
LATENCY_P95_THRESHOLD: float = 500.0

# Error rate: fraction (0.0–1.0) above which an alert fires.
# 0.05 == 5 %
ERROR_RATE_THRESHOLD: float = 0.05
