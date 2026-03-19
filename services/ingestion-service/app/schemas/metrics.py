import os
import sys
from typing import List
from pydantic import BaseModel, ConfigDict


# Resolve path to shared-libraries relative to service root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared-libraries")))

# Fallback if shared schema not available
from pydantic import BaseModel, Field, ConfigDict

class BaseMetric(BaseModel):
    endpoint_id: str = Field(..., description="Unique ID of the monitored API")
    timestamp: int = Field(..., description="Unix epoch timestamp in seconds")
    latency: float = Field(..., description="Response time in milliseconds")
    status_code: int = Field(..., description="HTTP response status")
    region: str = Field(..., description="Deployment region of the probe")

    # Enforce strict validation (no type coercion)
    model_config = ConfigDict(strict=True)

