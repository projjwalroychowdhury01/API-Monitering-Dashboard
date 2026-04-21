import os
import sys

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from clickhouse_driver import Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.metadata_store import MetadataStore

from app.config import settings


store = MetadataStore(settings.DATABASE_URL)
store.ensure_schema()
client = Client(
    host=settings.CLICKHOUSE_HOST,
    port=settings.CLICKHOUSE_PORT,
    user=settings.CLICKHOUSE_USER,
    password=settings.CLICKHOUSE_PASSWORD,
    database=settings.CLICKHOUSE_DB,
)

app = FastAPI(title="anomaly-engine Service", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "anomaly-engine"}


@app.get("/v1/anomalies")
async def get_anomalies(org_id: str = Query("demo-tenant"), minutes: int = Query(60, gt=0, le=1440)):
    latest_rows = client.execute(
        """
        SELECT tenant_id, service_name, endpoint_id, timestamp, p95, error_rate
        FROM metrics_1m
        WHERE tenant_id = %(tenant_id)s
          AND timestamp >= now() - INTERVAL %(minutes)s MINUTE
        ORDER BY timestamp DESC
        """,
        {"tenant_id": org_id, "minutes": minutes},
    )
    rules = store.list_alert_rules(org_id)

    latency_warning = _threshold_for(rules, "p95_latency", "warning", 500.0)
    latency_critical = _threshold_for(rules, "p95_latency", "critical", 1000.0)
    error_warning = _threshold_for(rules, "error_rate", "warning", 0.05)
    error_critical = _threshold_for(rules, "error_rate", "critical", 0.15)

    anomalies: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in latest_rows:
        _, service_name, endpoint_id, timestamp, p95, error_rate = row
        key = (service_name, endpoint_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        if p95 >= latency_critical:
            anomalies.append(
                _anomaly(
                    "latency",
                    "critical",
                    service_name,
                    endpoint_id,
                    float(p95),
                    latency_critical,
                    timestamp.isoformat(),
                    f"p95 latency {float(p95):.2f}ms exceeded critical threshold.",
                )
            )
        elif p95 >= latency_warning:
            anomalies.append(
                _anomaly(
                    "latency",
                    "warning",
                    service_name,
                    endpoint_id,
                    float(p95),
                    latency_warning,
                    timestamp.isoformat(),
                    f"p95 latency {float(p95):.2f}ms exceeded warning threshold.",
                )
            )

        if error_rate >= error_critical:
            anomalies.append(
                _anomaly(
                    "error_rate",
                    "critical",
                    service_name,
                    endpoint_id,
                    float(error_rate),
                    error_critical,
                    timestamp.isoformat(),
                    f"error rate {float(error_rate):.2%} exceeded critical threshold.",
                )
            )
        elif error_rate >= error_warning:
            anomalies.append(
                _anomaly(
                    "error_rate",
                    "warning",
                    service_name,
                    endpoint_id,
                    float(error_rate),
                    error_warning,
                    timestamp.isoformat(),
                    f"error rate {float(error_rate):.2%} exceeded warning threshold.",
                )
            )

    return {"status": "success", "data": anomalies}


def _threshold_for(rules, metric_name: str, severity: str, default: float) -> float:
    for rule in rules:
        if rule.metric_name == metric_name and rule.severity.lower() == severity:
            return float(rule.threshold)
    return default


def _anomaly(
    anomaly_type: str,
    severity: str,
    service_name: str,
    endpoint_id: str,
    current_value: float,
    threshold: float,
    timestamp: str,
    message: str,
) -> dict:
    return {
        "type": anomaly_type,
        "severity": severity,
        "service_name": service_name,
        "endpoint_id": endpoint_id,
        "current_value": current_value,
        "threshold": threshold,
        "timestamp": timestamp,
        "message": message,
    }
