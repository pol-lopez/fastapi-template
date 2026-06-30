from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="secrets/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Application Settings
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["console", "json"] = Field(
        default="console",
        description=(
            "Log output format: 'console' (human-readable) or 'json' (structured)"
        ),
    )

    # Security Settings
    secret_key: SecretStr = Field(
        default="changeme-insecure-secret-key",
        description="Secret key for signing tokens (CHANGE IN PRODUCTION!)",
    )
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )

    # Rate Limiting Settings
    rate_limit_requests: int = Field(
        default=100,
        description="Maximum requests per window",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit window duration in seconds",
    )
    rate_limit_exclude_paths: list[str] = Field(
        default=["/health", "/health/live"],
        description="Paths excluded from rate limiting",
    )

    # Database Settings
    database_url: str = Field(
        description="Database connection URL",
    )
    database_pool_size: int = Field(
        default=5,
        description="Persistent connections per worker. "
        "Keep workers * (pool_size + max_overflow) <= Postgres max_connections.",
    )
    database_max_overflow: int = Field(
        default=10,
        description="Extra burst connections per worker beyond pool_size.",
    )
    database_command_timeout: float | None = Field(
        default=30.0,
        description="Per-query timeout (seconds) for asyncpg; None disables it. "
        "Stops a runaway query from pinning a pool connection.",
    )

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Feature Flags (example)
    # enable_metrics: bool = Field(
    #     default=True,
    #     description="Enable metrics collection",
    # )

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
