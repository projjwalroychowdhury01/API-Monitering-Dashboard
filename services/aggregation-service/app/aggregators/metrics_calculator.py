import numpy as np


def calculate_metrics(events):
    if not events:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "request_count": 0,
            "error_rate": 0.0,
        }

    latencies = [float(e.get("latency_ms", e.get("latency", 0.0))) for e in events]
    status_codes = [int(e.get("status_code", 0) or 0) for e in events]

    errors = [status for status in status_codes if status == 0 or status >= 500]

    return {
        "p50": float(np.percentile(latencies, 50)),
        "p95": float(np.percentile(latencies, 95)),
        "p99": float(np.percentile(latencies, 99)),
        "request_count": len(events),
        "error_rate": len(errors) / len(events),
    }
