from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Base configuration for any microservice.
    Overridable via environment variables or .env file.
    """
    SERVICE_NAME: str = "ingestion-service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:29092"
    KAFKA_TOPIC_METRICS: str = "metrics_raw"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
