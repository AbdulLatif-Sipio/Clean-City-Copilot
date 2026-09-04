import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env file.
    """
    APP_NAME: str = "CleanCity Copilot API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./cleancity.db"

    # Security & Auth
    ADMIN_API_KEY: str = "cleancity-admin-secret-key-2026"

    # Rate Limiting
    SUBMIT_RATE_LIMIT: str = "10/minute"

    # Storage & Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_DIR: str = "media"
    IMAGE_SUBDIR: str = "media/images"
    AUDIO_SUBDIR: str = "media/audio"

    # Geo-Deduplication Parameters
    GEO_DEDUP_RADIUS_METERS: float = 50.0
    GEO_DEDUP_TIME_WINDOW_HOURS: float = 48.0

    # CORS settings (allowed origins for Streamlit citizen portal and admin dashboard)
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000"

    # AI Pipeline
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


# Global singleton settings instance
settings = Settings()
