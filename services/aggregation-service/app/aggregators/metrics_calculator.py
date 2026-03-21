import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from app.config import logger

class MetricsCalculator:
    @staticmethod
    def calculate_window_metrics(
        endpoint_id: str,
        window_start: datetime,
        region: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates aggregate metrics for a given window.
        Assumes all records belong to the same endpoint and region.
        """
        if not records:
            return None

        total_requests = len(records)
        latencies = [r['latency'] for r in records if 'latency' in r]
        
        # Calculate errors (status_code >= 400 counts as error for simple tracking)
        error_count = sum(1 for r in records if r.get('status_code', 200) >= 400)
        error_rate = error_count / total_requests if total_requests > 0 else 0.0

        if latencies:
            latencies_arr = np.array(latencies)
            avg_latency = float(np.mean(latencies_arr))
            min_latency = float(np.min(latencies_arr))
            max_latency = float(np.max(latencies_arr))
            p50_latency = float(np.percentile(latencies_arr, 50))
            p90_latency = float(np.percentile(latencies_arr, 90))
            p99_latency = float(np.percentile(latencies_arr, 99))
        else:
            avg_latency = min_latency = max_latency = p50_latency = p90_latency = p99_latency = 0.0

        return {
            "endpoint_id": endpoint_id,
            "window_start": window_start,
            "total_requests": total_requests,
            "error_count": error_count,
            "error_rate": error_rate,
            "avg_latency": avg_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "p50_latency": p50_latency,
            "p90_latency": p90_latency,
            "p99_latency": p99_latency,
            "region": region
        }
