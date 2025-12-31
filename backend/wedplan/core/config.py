"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Application name.
        app_version: Application version.
        debug: Enable debug mode.
        log_level: Logging level.
        default_time_limit: Default solver time limit in seconds.
        default_num_workers: Default number of solver workers.
    """

    model_config = SettingsConfigDict(
        env_prefix="WEDPLAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WedPlan"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    default_time_limit: float = 5.0
    default_num_workers: int = 1


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()
