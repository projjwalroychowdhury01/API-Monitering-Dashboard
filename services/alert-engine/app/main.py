# main.py
# Alert Engine entry-point.
# Polls ClickHouse for latest per-endpoint metrics, evaluates alert rules,
# deduplicates repeated alerts, and emits console alerts.
# Runs forever; never crashes.

import logging
import time
from typing import Any, Dict, List

from app.config import POLL_INTERVAL
from app.db.clickhouse_client import get_client, reset_client
from app.evaluators.evaluator import evaluate
from app.notifier.notifier import send_alerts
import app.alert_state as alert_state

# ---------------------------------------------------------------------------
# Logging — structured, timestamp-prefixed, stdlib only
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

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

    On any query failure the client singleton is reset (so the next cycle
    retries the connection) and an empty list is returned — the engine
    continues polling.

    Returns
    -------
    list[dict]
        Each dict has keys: endpoint_id (str), p95 (float), error_rate (float).
        Empty list on error or when the table has no rows.
    """
    try:
        client = get_client()
        data, columns = client.execute(_FETCH_SQL, with_column_types=True)
        col_names = [col[0] for col in columns]

        if not data:
            logger.debug("metrics_1m returned 0 rows.")
            return []

        return [dict(zip(col_names, row)) for row in data]

    except Exception as exc:
        logger.error("Failed to fetch metrics: %s", exc)
        reset_client()  # force reconnect on next cycle
        return []


def run_poll_cycle() -> None:
    """
    Single polling iteration:
    1. Fetch metrics from ClickHouse.
    2. Evaluate each endpoint against two-tier alert rules.
    3. Suppress alerts that are still within the cooldown window.
    4. Dispatch unsuppressed alerts to the notifier and record them.
    """
    logger.info("Polling cycle started.")

    metrics_list = fetch_latest_metrics()
    logger.info("Endpoints processed: %d", len(metrics_list))

    for metrics in metrics_list:
        endpoint_id: str = metrics.get("endpoint_id", "<unknown>")
        alerts = evaluate(metrics)

        # Filter out alerts still within the cooldown window.
        to_fire = []
        for alert in alerts:
            if alert_state.is_suppressed(endpoint_id, alert.type):
                logger.debug(
                    "Suppressed [%s] %s | %s (within cooldown)",
                    alert.severity, endpoint_id, alert.message,
                )
            else:
                to_fire.append(alert)

        # Dispatch and record each alert that passed deduplication.
        if to_fire:
            send_alerts(endpoint_id, to_fire)
            for alert in to_fire:
                alert_state.record_alert(endpoint_id, alert.type)


def main() -> None:
    """
    Infinite alert loop.
    Sleeps for POLL_INTERVAL seconds between cycles.
    Sleep always executes via finally — the engine never crashes.
    """
    logger.info("Alert Engine started. Poll interval: %ds.", POLL_INTERVAL)

    while True:
        try:
            run_poll_cycle()
        except Exception as exc:
            # Safety net: catch anything that escapes run_poll_cycle.
            logger.exception("Unexpected error in poll cycle: %s", exc)
        finally:
            # Always sleep — prevents tight retry loops on repeated failures.
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
