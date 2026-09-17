"""Application Configuration Management"""
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings"""

    # Project
    PROJECT_NAME: str = "AlphaLens"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]

    # Groq API
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TEMPERATURE: float = 0.3
    # Kept modest: several agents can call the LLM concurrently (parallel graph
    # fan-out), and free-tier Groq accounts share a per-minute token budget
    # across all of them, so an oversized default here causes 413s under load.
    GROQ_MAX_TOKENS: int = 2048
    GROQ_TIMEOUT: int = 60

    # Database (reserved for a future persistence phase)
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    QDRANT_URL: Optional[str] = None

    # External APIs
    FINANCIAL_DATA_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    SEC_USER_AGENT: str = "AlphaLens Research Platform (contact@example.com)"

    # Security
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Redis
    REDIS_CACHE_TTL: int = 300

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        """Accept a JSON list, a comma-separated string, or a single origin."""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                import json
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @field_validator("FINANCIAL_DATA_API_KEY", "NEWS_API_KEY", "GROQ_API_KEY", "DATABASE_URL", "QDRANT_URL", mode="before")
    @classmethod
    def _blank_to_none(cls, value):
        """Treat an empty-string env var the same as an unset one."""
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
