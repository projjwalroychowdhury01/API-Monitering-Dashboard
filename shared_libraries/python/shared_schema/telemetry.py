from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TelemetryEvent(BaseModel):
    """
    Standard schema for all telemetry events in the platform.
    Ensures data consistency from Probe -> ClickHouse.
    """
    endpoint_id: str = Field(..., description="Unique identifier for the monitored API")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of measurement")
    latency_ms: float = Field(..., description="Total response latency in milliseconds")
    status_code: int = Field(..., description="HTTP status code received")
    region: str = Field(..., description="Geographic region of the probe (e.g., us-east-1, eu-central-1)")
    
    # Optional metadata
    dns_lookup_ms: Optional[float] = None
    tcp_connect_ms: Optional[float] = None
    tls_handshake_ms: Optional[float] = None
    payload_size_bytes: Optional[int] = None
    cache_hit: Optional[bool] = None

class IngestionRequest(BaseModel):
    """
    Schema for raw metrics sent from probes to the ingestion gateway.
    """
    endpoint_id: str
    latency: float
    status: int
    region: str
    metadata: Optional[dict] = None
