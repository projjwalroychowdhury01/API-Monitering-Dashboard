import json
from datetime import datetime

from clickhouse_driver import Client

from app.config import settings


def get_client() -> Client:
    return Client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DB,
    )


def ensure_tables() -> None:
    client = get_client()
    client.execute(f"CREATE DATABASE IF NOT EXISTS {settings.CLICKHOUSE_DB}")
    statements = [
        """
        CREATE TABLE IF NOT EXISTS metrics_1m (
            tenant_id String,
            environment String,
            service_name String,
            endpoint_id String,
            region String,
            timestamp DateTime,
            p50 Float32,
            p95 Float32,
            p99 Float32,
            request_count UInt32,
            error_rate Float32
        )
        ENGINE = MergeTree()
        PARTITION BY toDate(timestamp)
        ORDER BY (tenant_id, endpoint_id, timestamp)
        TTL timestamp + INTERVAL 30 DAY
        """,
        """
        CREATE TABLE IF NOT EXISTS trace_spans (
            tenant_id String,
            environment String,
            service_name String,
            endpoint_id String,
            trace_id String,
            span_id String,
            parent_span_id String,
            parent_service_name String,
            started_at DateTime,
            latency_ms Float32,
            status_code Int32,
            attributes String,
            resource_attributes String
        )
        ENGINE = MergeTree()
        PARTITION BY toDate(started_at)
        ORDER BY (tenant_id, trace_id, started_at)
        TTL started_at + INTERVAL 14 DAY
        """,
        """
        CREATE TABLE IF NOT EXISTS log_events (
            tenant_id String,
            environment String,
            service_name String,
            endpoint_id String,
            trace_id String,
            timestamp DateTime,
            severity String,
            message String,
            attributes String
        )
        ENGINE = MergeTree()
        PARTITION BY toDate(timestamp)
        ORDER BY (tenant_id, service_name, timestamp)
        TTL timestamp + INTERVAL 14 DAY
        """,
        """
        CREATE TABLE IF NOT EXISTS service_graph_edges (
            tenant_id String,
            environment String,
            source_service String,
            target_service String,
            endpoint_id String,
            trace_id String,
            span_id String,
            timestamp DateTime
        )
        ENGINE = MergeTree()
        PARTITION BY toDate(timestamp)
        ORDER BY (tenant_id, source_service, target_service, timestamp)
        TTL timestamp + INTERVAL 14 DAY
        """,
    ]

    for statement in statements:
        client.execute(statement)


def insert_metrics_rollup(key, metrics):
    tenant_id, environment, service_name, endpoint_id, region = key
    client = get_client()
    client.execute(
        """
        INSERT INTO metrics_1m (
            tenant_id, environment, service_name, endpoint_id, region, timestamp,
            p50, p95, p99, request_count, error_rate
        ) VALUES
        """,
        [
            (
                tenant_id,
                environment,
                service_name,
                endpoint_id,
                region,
                datetime.utcnow(),
                metrics["p50"],
                metrics["p95"],
                metrics["p99"],
                metrics["request_count"],
                metrics["error_rate"],
            )
        ],
    )


def insert_trace_span(event):
    client = get_client()
    client.execute(
        """
        INSERT INTO trace_spans (
            tenant_id, environment, service_name, endpoint_id, trace_id, span_id,
            parent_span_id, parent_service_name, started_at, latency_ms, status_code,
            attributes, resource_attributes
        ) VALUES
        """,
        [
            (
                event["tenant_id"],
                event["environment"],
                event["service_name"],
                event.get("endpoint_id") or "",
                event.get("trace_id") or "",
                event.get("span_id") or "",
                event.get("parent_span_id") or "",
                event.get("parent_service_name") or "",
                _coerce_datetime(event["timestamp"]),
                float(event.get("latency_ms") or 0.0),
                int(event.get("status_code") or 0),
                json.dumps(event.get("attributes", {}), default=str),
                json.dumps(event.get("resource_attributes", {}), default=str),
            )
        ],
    )


def insert_log_event(event):
    client = get_client()
    client.execute(
        """
        INSERT INTO log_events (
            tenant_id, environment, service_name, endpoint_id, trace_id, timestamp,
            severity, message, attributes
        ) VALUES
        """,
        [
            (
                event["tenant_id"],
                event["environment"],
                event["service_name"],
                event.get("endpoint_id") or "",
                event.get("trace_id") or "",
                _coerce_datetime(event["timestamp"]),
                event.get("severity") or "info",
                event.get("message") or "",
                json.dumps(event.get("attributes", {}), default=str),
            )
        ],
    )


def insert_service_graph_edge(event):
    if not event.get("parent_service_name"):
        return

    client = get_client()
    client.execute(
        """
        INSERT INTO service_graph_edges (
            tenant_id, environment, source_service, target_service, endpoint_id,
            trace_id, span_id, timestamp
        ) VALUES
        """,
        [
            (
                event["tenant_id"],
                event["environment"],
                event["parent_service_name"],
                event["service_name"],
                event.get("endpoint_id") or "",
                event.get("trace_id") or "",
                event.get("span_id") or "",
                _coerce_datetime(event["timestamp"]),
            )
        ],
    )


def _coerce_datetime(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return datetime.utcfromtimestamp(value)
