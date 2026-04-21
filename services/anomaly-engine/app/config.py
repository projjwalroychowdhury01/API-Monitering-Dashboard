import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.service_settings import CommonSettings


class Settings(CommonSettings):
    SERVICE_NAME: str = "anomaly-engine"
    PORT: int = 8004


settings = Settings()
