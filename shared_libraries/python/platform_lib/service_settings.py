from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SQLITE_URL = f"sqlite:///{(_REPO_ROOT / 'data' / 'platform_metadata.sqlite3').as_posix()}"


class CommonSettings(BaseSettings):
    SERVICE_NAME: str = "platform-service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    ALLOWED_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = _DEFAULT_SQLITE_URL

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:29092"
    KAFKA_TOPIC_RAW_METRICS: str = "metrics_raw"
    KAFKA_TOPIC_TELEMETRY: str = "telemetry_events"

    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_DB: str = "observability"
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CHANNEL_PLATFORM_EVENTS: str = "platform.events"

    JWT_SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    RCA_PROVIDER: str = "heuristic"
    RCA_PROVIDER_URL: str | None = None
    RCA_PROVIDER_API_KEY: str | None = None
    RCA_MODEL: str = "incident-rca-v1"

    REPLAY_STORAGE_MODE: str = "local"
    REPLAY_STORAGE_PATH: str = Field(default_factory=lambda: str(_REPO_ROOT / "data" / "replay"))
    REPLAY_S3_BUCKET: str | None = None
    REPLAY_MAX_BODY_BYTES: int = 16_384

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite:///")

    @property
    def sqlite_path(self) -> Path:
        return Path(self.DATABASE_URL.replace("sqlite:///", "", 1))
