from __future__ import annotations

import json

from app.db.clickhouse_client import get_client


def get_endpoint_metrics(tenant_id: str, endpoint_id: str, time_range_minutes: int) -> dict:
    client = get_client()
    query = """
        SELECT
            avg(p50) AS p50,
            avg(p95) AS p95,
            avg(p99) AS p99,
            sum(request_count) AS request_count,
            avg(error_rate) AS error_rate
        FROM metrics_1m
        WHERE tenant_id = %(tenant_id)s
          AND endpoint_id = %(endpoint_id)s
          AND timestamp >= now() - INTERVAL %(minutes)s MINUTE
    """

    result = client.execute(query, {"tenant_id": tenant_id, "endpoint_id": endpoint_id, "minutes": time_range_minutes})
    if result and result[0]:
        row = result[0]
        return {
            "p50": float(row[0] or 0.0),
            "p95": float(row[1] or 0.0),
            "p99": float(row[2] or 0.0),
            "request_count": int(row[3] or 0),
            "error_rate": float(row[4] or 0.0),
        }
    return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "request_count": 0, "error_rate": 0.0}


def get_latency_history(tenant_id: str, endpoint_id: str, minutes: int) -> list[dict]:
    client = get_client()
    rows = client.execute(
        """
        SELECT timestamp, p50, p95, p99, request_count, error_rate
        FROM metrics_1m
        WHERE tenant_id = %(tenant_id)s
          AND endpoint_id = %(endpoint_id)s
          AND timestamp >= now() - INTERVAL %(minutes)s MINUTE
        ORDER BY timestamp ASC
        """,
        {"tenant_id": tenant_id, "endpoint_id": endpoint_id, "minutes": minutes},
    )
    return [
        {
            "timestamp": row[0].isoformat(),
            "p50": float(row[1]),
            "p95": float(row[2]),
            "p99": float(row[3]),
            "request_count": int(row[4]),
            "error_rate": float(row[5]),
        }
        for row in rows
    ]


def search_traces(tenant_id: str, minutes: int = 60, service_name: str | None = None, limit: int = 50) -> list[dict]:
    client = get_client()
    service_filter = "AND service_name = %(service_name)s" if service_name else ""
    rows = client.execute(
        f"""
        SELECT trace_id, service_name, endpoint_id, min(started_at), max(latency_ms), avg(latency_ms), any(status_code)
        FROM trace_spans
        WHERE tenant_id = %(tenant_id)s
          AND started_at >= now() - INTERVAL %(minutes)s MINUTE
          {service_filter}
        GROUP BY trace_id, service_name, endpoint_id
        ORDER BY min(started_at) DESC
        LIMIT %(limit)s
        """,
        {"tenant_id": tenant_id, "minutes": minutes, "service_name": service_name, "limit": limit},
    )
    return [
        {
            "trace_id": row[0],
            "service_name": row[1],
            "endpoint_id": row[2],
            "started_at": row[3].isoformat(),
            "max_latency_ms": float(row[4] or 0.0),
            "avg_latency_ms": float(row[5] or 0.0),
            "status_code": int(row[6] or 0),
        }
        for row in rows
    ]


def get_trace_detail(tenant_id: str, trace_id: str) -> list[dict]:
    client = get_client()
    rows = client.execute(
        """
        SELECT service_name, endpoint_id, span_id, parent_span_id, parent_service_name, started_at,
               latency_ms, status_code, attributes, resource_attributes
        FROM trace_spans
        WHERE tenant_id = %(tenant_id)s
          AND trace_id = %(trace_id)s
        ORDER BY started_at ASC
        """,
        {"tenant_id": tenant_id, "trace_id": trace_id},
    )
    return [
        {
            "service_name": row[0],
            "endpoint_id": row[1],
            "span_id": row[2],
            "parent_span_id": row[3],
            "parent_service_name": row[4],
            "started_at": row[5].isoformat(),
            "latency_ms": float(row[6] or 0.0),
            "status_code": int(row[7] or 0),
            "attributes": json.loads(row[8] or "{}"),
            "resource_attributes": json.loads(row[9] or "{}"),
        }
        for row in rows
    ]


def get_service_graph(tenant_id: str, minutes: int = 60) -> list[dict]:
    client = get_client()
    rows = client.execute(
        """
        SELECT source_service, target_service, endpoint_id, count(), max(timestamp)
        FROM service_graph_edges
        WHERE tenant_id = %(tenant_id)s
          AND timestamp >= now() - INTERVAL %(minutes)s MINUTE
        GROUP BY source_service, target_service, endpoint_id
        ORDER BY count() DESC
        """,
        {"tenant_id": tenant_id, "minutes": minutes},
    )
    return [
        {
            "source_service": row[0],
            "target_service": row[1],
            "endpoint_id": row[2],
            "edge_count": int(row[3]),
            "last_seen_at": row[4].isoformat(),
        }
        for row in rows
    ]


def get_recent_logs(tenant_id: str, minutes: int = 60, limit: int = 50) -> list[dict]:
    client = get_client()
    rows = client.execute(
        """
        SELECT service_name, endpoint_id, trace_id, timestamp, severity, message, attributes
        FROM log_events
        WHERE tenant_id = %(tenant_id)s
          AND timestamp >= now() - INTERVAL %(minutes)s MINUTE
        ORDER BY timestamp DESC
        LIMIT %(limit)s
        """,
        {"tenant_id": tenant_id, "minutes": minutes, "limit": limit},
    )
    return [
        {
            "service_name": row[0],
            "endpoint_id": row[1],
            "trace_id": row[2],
            "timestamp": row[3].isoformat(),
            "severity": row[4],
            "message": row[5],
            "attributes": json.loads(row[6] or "{}"),
        }
        for row in rows
    ]
