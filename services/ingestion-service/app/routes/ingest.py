from typing import Any

from fastapi import APIRouter, Depends, Request, status

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared_libraries/python")))

from platform_lib.metadata_store import ApiKeyRecord
from platform_lib.telemetry import TelemetryBatch, TelemetryEnvelope, normalize_legacy_metric

from app.config import settings
from app.dependencies import authenticate_ingest_key
from app.kafka.simple_producer import send_event
from app.schemas.metrics import BaseMetric


router = APIRouter(tags=["ingestion"])


@router.post("/ingest/metrics", status_code=status.HTTP_202_ACCEPTED)
async def ingest_legacy_metrics(metrics: list[BaseMetric], request: Request):
    producer = request.app.state.producer
    accepted = 0

    for metric in metrics:
        legacy_payload = metric.model_dump(mode="json")
        normalized = normalize_legacy_metric(
            {
                "endpoint_id": metric.endpoint_id,
                "timestamp": metric.timestamp,
                "latency": metric.latency,
                "status_code": metric.status_code,
                "region": metric.region,
            }
        )

        send_event(producer, settings.KAFKA_TOPIC_RAW_METRICS, legacy_payload)
        send_event(producer, settings.KAFKA_TOPIC_TELEMETRY, normalized.model_dump(mode="json"))
        accepted += 1

    return {"status": "success", "data": {"accepted": accepted, "mode": "legacy-compat"}}


@router.post("/v1/ingest/metrics", status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(
    batch: TelemetryBatch,
    request: Request,
    api_key: ApiKeyRecord = Depends(authenticate_ingest_key),
):
    return await _publish_batch(batch.events, request, api_key)


@router.post("/v1/ingest/traces", status_code=status.HTTP_202_ACCEPTED)
async def ingest_traces(
    batch: TelemetryBatch,
    request: Request,
    api_key: ApiKeyRecord = Depends(authenticate_ingest_key),
):
    return await _publish_batch(batch.events, request, api_key, expected_signal="trace")


@router.post("/v1/ingest/logs", status_code=status.HTTP_202_ACCEPTED)
async def ingest_logs(
    batch: TelemetryBatch,
    request: Request,
    api_key: ApiKeyRecord = Depends(authenticate_ingest_key),
):
    return await _publish_batch(batch.events, request, api_key, expected_signal="log")


async def _publish_batch(
    events: list[TelemetryEnvelope],
    request: Request,
    api_key: ApiKeyRecord,
    expected_signal: str | None = None,
) -> dict[str, Any]:
    producer = request.app.state.producer
    accepted = 0

    for event in events:
        if expected_signal and event.signal_type != expected_signal:
            continue

        if event.tenant_id != api_key.org_id:
            continue

        send_event(producer, settings.KAFKA_TOPIC_TELEMETRY, event.model_dump(mode="json"))
        accepted += 1

    return {"status": "success", "data": {"accepted": accepted, "org_id": api_key.org_id}}
