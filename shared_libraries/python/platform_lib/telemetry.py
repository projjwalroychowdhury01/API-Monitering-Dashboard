from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


SignalType = Literal["metric", "trace", "log"]
SourceType = Literal[
    "synthetic_probe",
    "otel_metric",
    "otel_trace",
    "otel_log",
    "application",
    "replay",
]


class RequestCapture(BaseModel):
    method: str = "GET"
    path: str | None = None
    url: str | None = None
    headers: dict[str, Any] = Field(default_factory=dict)
    body: Any | None = None


class TelemetryEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    signal_type: SignalType
    source_type: SourceType
    tenant_id: str
    environment: str
    service_name: str
    endpoint_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    latency_ms: float | None = None
    status_code: int | None = None
    region: str | None = None

    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    parent_service_name: str | None = None

    severity: str | None = None
    message: str | None = None

    resource_attributes: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: dict[str, Any] = Field(default_factory=dict)
    request: RequestCapture | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _coerce_timestamp(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return value


class TelemetryBatch(BaseModel):
    events: list[TelemetryEnvelope]


class LegacyProbeMetric(BaseModel):
    endpoint_id: str
    timestamp: datetime | int | float
    latency: float
    status_code: int
    region: str


def normalize_legacy_metric(
    metric: LegacyProbeMetric | dict[str, Any],
    tenant_id: str = "demo-tenant",
    environment: str = "development",
    service_name: str = "probe-workers",
) -> TelemetryEnvelope:
    model = metric if isinstance(metric, LegacyProbeMetric) else LegacyProbeMetric.model_validate(metric)
    return TelemetryEnvelope(
        signal_type="metric",
        source_type="synthetic_probe",
        tenant_id=tenant_id,
        environment=environment,
        service_name=service_name,
        endpoint_id=model.endpoint_id,
        timestamp=model.timestamp,
        latency_ms=model.latency * 1000.0,
        status_code=model.status_code,
        region=model.region,
        attributes={"legacy": True},
    )
