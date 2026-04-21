from typing import Dict, Any

from fastapi import APIRouter, Query, Request

from app.dependencies import get_store
from app.services.query_service import (
    get_recent_logs,
    get_service_graph,
    get_trace_detail,
    search_traces,
)


router = APIRouter(prefix="/v1", tags=["query-plane"])


@router.get("/traces")
async def get_traces(
    request: Request,
    service_name: str | None = None,
    minutes: int = Query(60, gt=0, le=1440),
    limit: int = Query(50, gt=0, le=200),
) -> Dict[str, Any]:
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    return {"status": "success", "data": search_traces(tenant_id, minutes, service_name, limit)}


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str, request: Request) -> Dict[str, Any]:
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    return {"status": "success", "data": get_trace_detail(tenant_id, trace_id)}


@router.get("/services/graph")
async def get_services_graph(request: Request, minutes: int = Query(60, gt=0, le=1440)) -> Dict[str, Any]:
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    return {"status": "success", "data": get_service_graph(tenant_id, minutes)}


@router.get("/logs")
async def get_logs(request: Request, minutes: int = Query(60, gt=0, le=1440), limit: int = Query(50, gt=0, le=200)) -> Dict[str, Any]:
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    return {"status": "success", "data": get_recent_logs(tenant_id, minutes, limit)}


@router.get("/incidents")
async def read_incidents(request: Request):
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    store = get_store()
    return {"status": "success", "data": [incident.model_dump() for incident in store.list_incidents(tenant_id)]}


@router.get("/incidents/{incident_id}/timeline")
async def read_incident_timeline(incident_id: str):
    store = get_store()
    return {"status": "success", "data": [event.model_dump() for event in store.get_incident_timeline(incident_id)]}
