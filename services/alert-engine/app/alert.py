# alert.py
# Typed alert container shared across evaluator, notifier, and main.
# Pure data — no logic, no imports beyond stdlib dataclasses.

from dataclasses import dataclass


@dataclass(frozen=True)
class Alert:
    """
    Immutable record of a single fired alert.

    Attributes
    ----------
    type : str
        Alert category key used for deduplication.
        Values: "latency" | "error_rate"
    severity : str
        Urgency level.
        Values: "WARNING" | "CRITICAL"
    message : str
        Human-readable description, e.g. "High latency: p95=650ms".
    """
    type: str
    severity: str
    message: str
