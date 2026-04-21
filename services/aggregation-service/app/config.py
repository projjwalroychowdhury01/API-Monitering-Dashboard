import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.service_settings import CommonSettings


class Settings(CommonSettings):
    SERVICE_NAME: str = "aggregation-service"
    PORT: int = 8003
    KAFKA_GROUP_ID: str = "aggregation_service_group"
    AGGREGATION_WINDOW_SECONDS: int = 30
    LOG_LEVEL: str = "INFO"


settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(settings.SERVICE_NAME)
