from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas.metrics import Metric
from app.kafka.simple_producer import send_metric
from app.logger import logger

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(metrics: List[Metric]):
    """Accept a list of `Metric` objects, validate, and publish to Kafka."""
    try:
        sent = 0
        for m in metrics:
            # Convert to dict for the producer
            payload = m.model_dump()
            send_metric(payload)
            sent += 1

        logger.info("Metrics forwarded to Kafka", extra={"count": sent})

        return {"message": "Metrics accepted", "accepted": sent}

    except Exception as e:
        logger.error("Failed to forward metrics", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to forward metrics to Kafka"
        )
# @router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
# async def ingest_metrics(metrics: List[Metric]):
#     sent = 0
#     for m in metrics:
#         payload = m.model_dump()
#         send_metric(payload)
#         sent += 1

#     return {"message": "Metrics accepted", "accepted": sent}