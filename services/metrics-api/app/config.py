import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Base configuration for any microservice.
    Overridable via environment variables or .env file.
    """
    SERVICE_NAME: str = "base-service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
