from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class BaseMetric(BaseModel):
    """
    The foundational schema for all telemetry events.
    Ensures consistency from Probe -> Ingestion -> ClickHouse.
    """
    endpoint_id: str = Field(..., description="Unique ID of the monitored API")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float = Field(..., description="Response time in milliseconds")
    status_code: int = Field(..., description="HTTP response status")
    region: str = Field(..., description="Deployment region of the probe")
    
    # Optional performance breakdown
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MetricBatch(BaseModel):
    """Schema for batch processing of metrics."""
    metrics: list[BaseMetric]
    count: int
