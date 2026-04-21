from typing import Dict, Any

from fastapi import APIRouter, Query, HTTPException, Request

from app.config import settings
from app.services.cache_service import get, set as cache_set
from app.services.query_service import get_endpoint_metrics, get_latency_history


router = APIRouter()


@router.get("/metrics/latency")
async def get_latency_metrics(
    request: Request,
    endpoint_id: str = Query(..., min_length=1, description="The ID of the endpoint"),
    minutes: int = Query(60, gt=0, le=240, description="Time range in minutes"),
) -> Dict[str, Any]:
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    cache_key = f"metrics:latency:{tenant_id}:{endpoint_id}:{minutes}"

    try:
        cached_result = get(cache_key)
        if cached_result is not None:
            return {"status": "success", "data": cached_result}

        db_result = get_endpoint_metrics(tenant_id, endpoint_id, minutes)
        cache_set(cache_key, db_result, ttl=settings.CACHE_TTL_SECONDS)
        return {"status": "success", "data": db_result}
    except Exception as exc:
        print("ERROR:", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/v1/metrics/latency/history")
async def get_latency_history_route(
    request: Request,
    endpoint_id: str = Query(..., min_length=1),
    minutes: int = Query(60, gt=0, le=1440),
) -> Dict[str, Any]:
    tenant_id = request.headers.get("X-Tenant-ID", "demo-tenant")
    cache_key = f"metrics:latency:history:{tenant_id}:{endpoint_id}:{minutes}"
    cached_result = get(cache_key)
    if cached_result is not None:
        return {"status": "success", "data": cached_result}

    result = get_latency_history(tenant_id, endpoint_id, minutes)
    cache_set(cache_key, result, ttl=settings.CACHE_TTL_SECONDS)
    return {"status": "success", "data": result}
