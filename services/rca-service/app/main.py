import os
import sys

from clickhouse_driver import Client
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.llm import HeuristicRCAProvider, HostedLLMProvider
from platform_lib.metadata_store import MetadataStore
from platform_lib.service_settings import CommonSettings


class Settings(CommonSettings):
    SERVICE_NAME: str = "rca-service"
    PORT: int = 8007


settings = Settings()
store = MetadataStore(settings.DATABASE_URL)
store.ensure_schema()
client = Client(
    host=settings.CLICKHOUSE_HOST,
    port=settings.CLICKHOUSE_PORT,
    user=settings.CLICKHOUSE_USER,
    password=settings.CLICKHOUSE_PASSWORD,
    database=settings.CLICKHOUSE_DB,
)

provider = (
    HostedLLMProvider(settings.RCA_PROVIDER_URL, settings.RCA_PROVIDER_API_KEY, settings.RCA_MODEL)
    if settings.RCA_PROVIDER == "hosted" and settings.RCA_PROVIDER_URL
    else HeuristicRCAProvider()
)

app = FastAPI(title="RCA Service", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/v1/rca/{incident_id}")
async def generate_rca(incident_id: str):
    incident = store.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found.")

    context = {
        "incident": incident.model_dump(),
        "timeline": [event.model_dump() for event in store.get_incident_timeline(incident_id)],
        "traces": _query_traces(incident.org_id),
        "logs": _query_logs(incident.org_id),
        "service_graph": _query_service_graph(incident.org_id),
        "anomalies": incident.evidence.get("alerts", []),
    }
    result = provider.generate(incident.model_dump(), context)
    return {
        "status": "success",
        "data": {
            "incident_id": incident_id,
            "summary": result.summary,
            "confidence": result.confidence,
            "evidence": result.evidence,
            "provider": result.provider,
        },
    }


def _query_traces(tenant_id: str) -> list[dict]:
    rows = client.execute(
        """
        SELECT trace_id, service_name, endpoint_id, started_at, latency_ms, status_code
        FROM trace_spans
        WHERE tenant_id = %(tenant_id)s
          AND started_at >= now() - INTERVAL 120 MINUTE
        ORDER BY started_at DESC
        LIMIT 25
        """,
        {"tenant_id": tenant_id},
    )
    return [
        {
            "trace_id": row[0],
            "service_name": row[1],
            "endpoint_id": row[2],
            "started_at": row[3].isoformat(),
            "latency_ms": float(row[4] or 0.0),
            "status_code": int(row[5] or 0),
        }
        for row in rows
    ]


def _query_logs(tenant_id: str) -> list[dict]:
    rows = client.execute(
        """
        SELECT service_name, endpoint_id, trace_id, timestamp, severity, message
        FROM log_events
        WHERE tenant_id = %(tenant_id)s
          AND timestamp >= now() - INTERVAL 120 MINUTE
        ORDER BY timestamp DESC
        LIMIT 25
        """,
        {"tenant_id": tenant_id},
    )
    return [
        {
            "service_name": row[0],
            "endpoint_id": row[1],
            "trace_id": row[2],
            "timestamp": row[3].isoformat(),
            "severity": row[4],
            "message": row[5],
        }
        for row in rows
    ]


def _query_service_graph(tenant_id: str) -> list[dict]:
    rows = client.execute(
        """
        SELECT source_service, target_service, endpoint_id, count()
        FROM service_graph_edges
        WHERE tenant_id = %(tenant_id)s
          AND timestamp >= now() - INTERVAL 120 MINUTE
        GROUP BY source_service, target_service, endpoint_id
        ORDER BY count() DESC
        LIMIT 25
        """,
        {"tenant_id": tenant_id},
    )
    return [
        {
            "source_service": row[0],
            "target_service": row[1],
            "endpoint_id": row[2],
            "edge_count": int(row[3]),
        }
        for row in rows
    ]
