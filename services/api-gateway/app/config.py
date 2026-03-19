import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Environment-based configuration for the API Gateway.
    Uses pydantic-settings for validation and automatic .env loading.
    """
    # Service Metadata
    SERVICE_NAME: str = "api-gateway"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Auth Settings (Placeholder for Phase 3)
    JWT_SECRET_KEY: str = "placeholder_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
