import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


def _load_endpoints():
    """Load endpoints configuration from a JSON file.

    This allows defining monitored endpoints outside of code.
    """
    path = Path(os.getenv("ENDPOINTS_PATH", "endpoints.json"))

    if path.exists():
        try:
            raw = json.loads(path.read_text())
            endpoints = raw.get("endpoints") or raw.get("endpoints", [])
            if isinstance(endpoints, list):
                return endpoints
        except Exception:
            pass

    # Fallback default
    return [{"id": "google-test", "url": os.getenv("TEST_TARGET", "https://google.com")}]


class Settings(BaseSettings):
    SERVICE_NAME: str = "probe-workers"
    REGION: str = os.getenv("REGION", "local-dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # The probe scheduler will read these endpoints and poll each one.
    ENDPOINTS: list[dict] = Field(default_factory=_load_endpoints)

    # Probe scheduling
    PROBE_INTERVAL_SECONDS: int = int(os.getenv("PROBE_INTERVAL_SECONDS", 30))

    # Probe request timeout (seconds)
    PROBE_TIMEOUT_SECONDS: int = int(os.getenv("PROBE_TIMEOUT_SECONDS", 10))

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
