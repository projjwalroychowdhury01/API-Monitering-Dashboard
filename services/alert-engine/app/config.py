import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.service_settings import CommonSettings


class Settings(CommonSettings):
    SERVICE_NAME: str = "alert-engine"
    PORT: int = 8005
    POLL_INTERVAL: int = 60
    ALERT_COOLDOWN: int = 300
    ALERT_WEBHOOK_URL: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 25
    SMTP_FROM: str = "alerts@localhost"


settings = Settings()
