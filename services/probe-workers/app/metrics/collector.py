from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProbeMetrics(BaseModel):
    dns_lookup: float = 0.0
    tcp_connect: float = 0.0
    tls_handshake: float = 0.0
    server_response: float = 0.0
    total_latency: float = 0.0

class ProbeResult(BaseModel):
    endpoint_id: str
    timestamp: datetime
    status_code: int
    latency: float  # total latency
    region: str
    metrics: ProbeMetrics
    error: Optional[str] = None


class TelemetryEvent(BaseModel):
    """
    Final telemetry schema returned by metrics collector.
    Standardized format for all telemetry events.
    """
    endpoint_id: str = Field(..., description="Unique identifier for the monitored API")
    timestamp: datetime = Field(..., description="Time of measurement")
    latency: float = Field(..., description="Total response latency")
    status_code: int = Field(..., description="HTTP status code received")
    region: str = Field(..., description="Geographic region of the probe")


class MetricsCollector:
    """
    Collects and enriches probe results into standardized telemetry events.
    
    Responsibilities:
    - Accept probe results from probe workers
    - Enrich with required metadata (timestamp, endpoint_id, region)
    - Validate and transform into telemetry schema
    - Return standardized telemetry events for downstream processing
    """
    
    DEFAULT_REGION = "local"
    
    def collect(self, probe_result: ProbeResult) -> TelemetryEvent:
        """
        Collect and enrich a probe result into a telemetry event.
        
        Args:
            probe_result: Raw probe result from probe worker
            
        Returns:
            TelemetryEvent: Enriched and standardized telemetry event
        """
        return TelemetryEvent(
            endpoint_id=probe_result.endpoint_id,
            timestamp=probe_result.timestamp,
            latency=probe_result.latency,
            status_code=probe_result.status_code,
            region=probe_result.region or self.DEFAULT_REGION
        )
