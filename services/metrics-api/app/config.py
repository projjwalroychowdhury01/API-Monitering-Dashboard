import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.service_settings import CommonSettings


class Settings(CommonSettings):
    SERVICE_NAME: str = "metrics-api"
    PORT: int = 8002
    CACHE_TTL_SECONDS: int = 30


settings = Settings()
