import numpy as np

def calculate_metrics(events):
    if not events:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "request_count": 0,
            "error_rate": 0.0
        }

    latencies = [e["latency"] for e in events]
    status_codes = [e["status_code"] for e in events]

    errors = [s for s in status_codes if s >= 500]

    return {
        "p50": float(np.percentile(latencies, 50)),
        "p95": float(np.percentile(latencies, 95)),
        "p99": float(np.percentile(latencies, 99)),
        "request_count": len(events),
        "error_rate": len(errors) / len(events)
    }
