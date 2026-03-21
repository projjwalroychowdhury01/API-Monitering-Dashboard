from fastapi import APIRouter, status, Request
from typing import List
from app.schemas.metrics import BaseMetric
from app.kafka.simple_producer import send_metric
from app.logger import logger #type: ignore

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(metrics: List[BaseMetric], request: Request):
    producer = request.app.state.producer

    sent = 0
    for m in metrics:
        payload = m.model_dump(mode="json")

        print("PAYLOAD:", payload)

        future = producer.send("metrics_raw", payload)

        # 🔥 THIS LINE IS CRITICAL
        result = future.get(timeout=10)

        print("KAFKA RESULT:", result)

        sent += 1

    return {"message": "Metrics accepted", "accepted": sent}