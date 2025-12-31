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
        cors_origins: Comma-separated list of allowed CORS origins.
        static_dir: Path to static files directory (built frontend).
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
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    static_dir: str = "dist"

    def get_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list.

        Returns:
            List of allowed origin URLs.
        """
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()
