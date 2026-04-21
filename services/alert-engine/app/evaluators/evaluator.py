from typing import Any, Dict, List

from app.alert import Alert


DEFAULT_THRESHOLDS = {
    ("p95_latency", "warning"): 500.0,
    ("p95_latency", "critical"): 1000.0,
    ("error_rate", "warning"): 0.05,
    ("error_rate", "critical"): 0.15,
}


def evaluate(metrics: Dict[str, Any], rules: list) -> List[Alert]:
    thresholds = DEFAULT_THRESHOLDS.copy()
    for rule in rules:
        thresholds[(rule.metric_name, rule.severity.lower())] = float(rule.threshold)

    alerts: List[Alert] = []
    p95 = float(metrics.get("p95") or 0.0)
    error_rate = float(metrics.get("error_rate") or 0.0)

    if p95 >= thresholds[("p95_latency", "critical")]:
        alerts.append(
            Alert(
                org_id=metrics["tenant_id"],
                service_name=metrics["service_name"],
                endpoint_id=metrics["endpoint_id"],
                type="latency",
                severity="critical",
                message=f"High latency: p95={p95:.2f}ms",
                current_value=p95,
                threshold=thresholds[("p95_latency", "critical")],
            )
        )
    elif p95 >= thresholds[("p95_latency", "warning")]:
        alerts.append(
            Alert(
                org_id=metrics["tenant_id"],
                service_name=metrics["service_name"],
                endpoint_id=metrics["endpoint_id"],
                type="latency",
                severity="warning",
                message=f"Latency regression: p95={p95:.2f}ms",
                current_value=p95,
                threshold=thresholds[("p95_latency", "warning")],
            )
        )

    if error_rate >= thresholds[("error_rate", "critical")]:
        alerts.append(
            Alert(
                org_id=metrics["tenant_id"],
                service_name=metrics["service_name"],
                endpoint_id=metrics["endpoint_id"],
                type="error_rate",
                severity="critical",
                message=f"High error rate: {error_rate:.2%}",
                current_value=error_rate,
                threshold=thresholds[("error_rate", "critical")],
            )
        )
    elif error_rate >= thresholds[("error_rate", "warning")]:
        alerts.append(
            Alert(
                org_id=metrics["tenant_id"],
                service_name=metrics["service_name"],
                endpoint_id=metrics["endpoint_id"],
                type="error_rate",
                severity="warning",
                message=f"Elevated error rate: {error_rate:.2%}",
                current_value=error_rate,
                threshold=thresholds[("error_rate", "warning")],
            )
        )

    return alerts
