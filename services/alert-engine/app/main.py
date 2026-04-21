import logging
import time
import os
import sys
from typing import Any, Dict, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.metadata_store import MetadataStore

from app.config import settings
from app.db.clickhouse_client import get_client, reset_client
from app.evaluators.evaluator import evaluate
from app.notifier.notifier import send_alerts
import app.alert_state as alert_state


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
store = MetadataStore(settings.DATABASE_URL)
store.ensure_schema()

_FETCH_SQL = """
SELECT tenant_id, service_name, endpoint_id, p95, error_rate
FROM metrics_1m
WHERE (tenant_id, endpoint_id, timestamp) IN (
    SELECT tenant_id, endpoint_id, max(timestamp)
    FROM metrics_1m
    GROUP BY tenant_id, endpoint_id
)
"""


def fetch_latest_metrics() -> List[Dict[str, Any]]:
    try:
        client = get_client()
        data, columns = client.execute(_FETCH_SQL, with_column_types=True)
        col_names = [column[0] for column in columns]
        return [dict(zip(col_names, row)) for row in data]
    except Exception as exc:
        logger.error("Failed to fetch metrics: %s", exc)
        reset_client()
        return []


def run_poll_cycle() -> None:
    logger.info("Polling cycle started.")
    metrics_list = fetch_latest_metrics()
    grouped_rules: dict[str, list] = {}

    for metrics in metrics_list:
        tenant_id = metrics["tenant_id"]
        if tenant_id not in grouped_rules:
            grouped_rules[tenant_id] = store.list_alert_rules(tenant_id)

        alerts = evaluate(metrics, grouped_rules[tenant_id])
        source_key = f"{tenant_id}:{metrics['service_name']}:{metrics['endpoint_id']}"

        to_fire = []
        for alert in alerts:
            if alert_state.is_suppressed(source_key, alert.type):
                continue
            to_fire.append(alert)

        if to_fire:
            severity_rank = {"warning": 1, "critical": 2}
            highest = sorted(to_fire, key=lambda item: severity_rank.get(item.severity.lower(), 0), reverse=True)[0]
            incident = store.upsert_incident(
                org_id=tenant_id,
                source_key=source_key,
                title=f"{highest.service_name} degradation detected",
                severity=highest.severity,
                summary=highest.message,
                evidence={"alerts": [alert.message for alert in to_fire]},
            )
            for alert in to_fire:
                alert_state.record_alert(source_key, alert.type)
                store.append_incident_event(
                    incident.id,
                    "alert-fired",
                    alert.message,
                    {
                        "type": alert.type,
                        "severity": alert.severity,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "service_name": alert.service_name,
                        "endpoint_id": alert.endpoint_id,
                    },
                )
            send_alerts(incident.id, to_fire)


def main() -> None:
    logger.info("Alert Engine started. Poll interval: %ds.", settings.POLL_INTERVAL)
    while True:
        try:
            run_poll_cycle()
        except Exception as exc:
            logger.exception("Unexpected error in poll cycle: %s", exc)
        finally:
            time.sleep(settings.POLL_INTERVAL)


if __name__ == "__main__":
    main()
