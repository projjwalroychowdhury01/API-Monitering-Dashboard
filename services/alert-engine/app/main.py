# main.py
# Alert Engine entry-point.
# Polls ClickHouse for latest per-endpoint metrics, evaluates alert rules,
# and emits console alerts.  Runs forever; never crashes.

import time
from typing import Any, Dict, List

from app.config import POLL_INTERVAL
from app.db.clickhouse_client import get_client
from app.evaluators.evaluator import evaluate
from app.notifier.notifier import send_alerts

# ---------------------------------------------------------------------------
# SQL — fetch the single most-recent row per endpoint
# ---------------------------------------------------------------------------
_FETCH_SQL = """
SELECT
    endpoint_id,
    p95,
    error_rate
FROM metrics_1m
WHERE (endpoint_id, timestamp) IN (
    SELECT endpoint_id, max(timestamp)
    FROM metrics_1m
    GROUP BY endpoint_id
)
"""


def fetch_latest_metrics() -> List[Dict[str, Any]]:
    """
    Query ClickHouse and return a list of metric dicts.

    Returns an empty list when there is no data or the query fails.
    Each dict has keys: endpoint_id (str), p95 (float), error_rate (float).
    """
    try:
        client = get_client()
        rows = client.execute(_FETCH_SQL, with_column_types=True)
        # rows == (data_rows, column_types) when with_column_types=True
        data, columns = rows
        col_names = [col[0] for col in columns]

        if not data:
            return []

        return [dict(zip(col_names, row)) for row in data]

    except Exception as exc:
        print(f"[ERROR] Failed to fetch metrics: {exc}")
        return []


def run_poll_cycle() -> None:
    """
    Single polling iteration:
    1. Fetch metrics from ClickHouse.
    2. Evaluate each endpoint against alert rules.
    3. Dispatch alerts to the notifier.
    """
    print("[INFO] Polling cycle started.")

    metrics_list = fetch_latest_metrics()
    print(f"[INFO] Endpoints processed: {len(metrics_list)}")

    for metrics in metrics_list:
        endpoint_id = metrics.get("endpoint_id", "<unknown>")
        alerts = evaluate(metrics)
        send_alerts(endpoint_id, alerts)


def main() -> None:
    """
    Infinite alert loop.
    Sleeps for POLL_INTERVAL seconds between cycles.
    Sleep always executes, even after an error — the engine never crashes.
    """
    print(f"[INFO] Alert Engine started. Poll interval: {POLL_INTERVAL}s.")

    while True:
        try:
            run_poll_cycle()
        except Exception as exc:
            # Catch any unexpected error so the loop continues.
            print(f"[ERROR] Unexpected error in poll cycle: {exc}")
        finally:
            # Always sleep — prevents tight retry loops on repeated failures.
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
