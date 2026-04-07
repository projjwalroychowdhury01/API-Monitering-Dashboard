# evaluators/evaluator.py
# Pure function: evaluate a single endpoint's metrics against two-tier thresholds.
# No side effects. Safe against None / missing / non-numeric values.

from typing import Any, Dict, List

from app.alert import Alert
from app.rules.rules import (
    ERROR_RATE_CRITICAL,
    ERROR_RATE_WARNING,
    LATENCY_P95_CRITICAL,
    LATENCY_P95_WARNING,
)


def evaluate(metrics: Dict[str, Any]) -> List[Alert]:
    """
    Evaluate a metrics dict and return a list of Alert objects.

    Parameters
    ----------
    metrics : dict
        Expected keys: "endpoint_id" (str), "p95" (float), "error_rate" (float).
        Missing or None values are treated as non-alerting (safe default).

    Returns
    -------
    list[Alert]
        Zero or more Alert objects, each carrying type, severity, and message.
        Empty list means no thresholds were breached.

    Severity rules (checked in ascending order; highest match wins):
        p95 > LATENCY_P95_WARNING  → WARNING
        p95 > LATENCY_P95_CRITICAL → CRITICAL
        error_rate > ERROR_RATE_WARNING  → WARNING
        error_rate > ERROR_RATE_CRITICAL → CRITICAL
    """
    alerts: List[Alert] = []

    p95 = metrics.get("p95")
    error_rate = metrics.get("error_rate")

    # ------------------------------------------------------------------
    # Latency check
    # ------------------------------------------------------------------
    if p95 is not None:
        try:
            p95_f = float(p95)
            if p95_f > LATENCY_P95_CRITICAL:
                alerts.append(Alert(
                    type="latency",
                    severity="CRITICAL",
                    message=f"High latency: p95={p95_f:.0f}ms",
                ))
            elif p95_f > LATENCY_P95_WARNING:
                alerts.append(Alert(
                    type="latency",
                    severity="WARNING",
                    message=f"High latency: p95={p95_f:.0f}ms",
                ))
        except (ValueError, TypeError):
            pass  # non-numeric value; do not alert

    # ------------------------------------------------------------------
    # Error rate check
    # ------------------------------------------------------------------
    if error_rate is not None:
        try:
            er_f = float(error_rate)
            if er_f > ERROR_RATE_CRITICAL:
                alerts.append(Alert(
                    type="error_rate",
                    severity="CRITICAL",
                    message=f"High error rate: {er_f:.2f}",
                ))
            elif er_f > ERROR_RATE_WARNING:
                alerts.append(Alert(
                    type="error_rate",
                    severity="WARNING",
                    message=f"High error rate: {er_f:.2f}",
                ))
        except (ValueError, TypeError):
            pass  # non-numeric value; do not alert

    return alerts
