from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import logging

class Settings(BaseSettings):
    # Kafka
    kafka_broker_url: str = Field(default="localhost:29092", env="KAFKA_BROKER_URL")
    kafka_topic_raw: str = Field(default="metrics_raw", env="KAFKA_TOPIC_RAW")
    kafka_group_id: str = Field(default="aggregation_service_group", env="KAFKA_GROUP_ID")

    # ClickHouse
    clickhouse_host: str = Field(default="localhost", env="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(default=9000, env="CLICKHOUSE_PORT")
    clickhouse_db: str = Field(default="marketviz", env="CLICKHOUSE_DB")
    clickhouse_user: str = Field(default="default", env="CLICKHOUSE_USER")
    clickhouse_password: str = Field(default="", env="CLICKHOUSE_PASSWORD")
    
    # App config
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    aggregation_window_seconds: int = Field(default=30, env="AGGREGATION_WINDOW_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aggregation-service")
