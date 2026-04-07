# evaluators/evaluator.py
# Pure function: evaluate a single endpoint's metrics against alert thresholds.
# No side effects. Safe against None / missing values.

from typing import Any, Dict, List

from app.rules.rules import ERROR_RATE_THRESHOLD, LATENCY_P95_THRESHOLD


def evaluate(metrics: Dict[str, Any]) -> List[str]:
    """
    Evaluate a metrics dict and return a list of alert message strings.

    Parameters
    ----------
    metrics : dict
        Expected keys: "endpoint_id" (str), "p95" (float), "error_rate" (float).
        Missing or None values are treated as non-alerting (safe default).

    Returns
    -------
    list[str]
        Zero or more alert message strings.
        Empty list means no alerts fired.
    """
    alerts: List[str] = []

    p95 = metrics.get("p95")
    error_rate = metrics.get("error_rate")

    # Latency check — skip if value is absent or not numeric
    if p95 is not None:
        try:
            if float(p95) > LATENCY_P95_THRESHOLD:
                alerts.append(f"High latency: p95={p95:.0f}ms")
        except (ValueError, TypeError):
            pass  # non-numeric value; do not alert

    # Error rate check — skip if value is absent or not numeric
    if error_rate is not None:
        try:
            if float(error_rate) > ERROR_RATE_THRESHOLD:
                alerts.append(f"High error rate: {error_rate:.2f}")
        except (ValueError, TypeError):
            pass  # non-numeric value; do not alert

    return alerts
