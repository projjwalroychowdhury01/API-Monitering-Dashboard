from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
from app.services.cache_service import get, set as cache_set
from app.services.query_service import get_endpoint_metrics

router = APIRouter()

@router.get("/metrics/latency")
async def get_latency_metrics(
    endpoint_id: str = Query(..., min_length=1, description="The ID of the endpoint"),
    minutes: int = Query(60, gt=0, le=1440, description="Time range in minutes")
) -> Dict[str, Any]:
    cache_key = f"metrics:latency:{endpoint_id}:{minutes}"
    
    try:
        # Check Redis cache
        cached_result = get(cache_key)
        if cached_result is not None:
            return {
                "status": "success",
                "data": cached_result
            }
            
        # If cache miss -> query ClickHouse
        db_result = get_endpoint_metrics(endpoint_id, minutes)
        
        # Store in cache
        cache_set(cache_key, db_result, ttl=60)
        
        # Return result
        return {
            "status": "success",
            "data": db_result
        }
    except Exception as e:
        print("ERROR:", e)  # Internal log only — not exposed to client
        raise HTTPException(status_code=500, detail="Internal server error")