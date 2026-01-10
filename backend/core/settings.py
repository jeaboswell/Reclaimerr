from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.__version__ import __version__
from backend.core.logger.levels import LogLevel


class Settings(BaseSettings):
    """Bootstrap settings loaded from environment variables.

    Note: Service credentials (Plex, Jellyfin, Radarr, Sonarr) are stored
    in the database (ServiceConfig table) and managed via the UI.
    """

    # application data directory
    data_dir: Path = Field(
        default=Path("./data"), description="Directory for database, logs, cache"
    )

    # logging
    log_level: str = Field(
        default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "*"  # comma-separated list or "*" for all

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        try:
            LogLevel[v.upper()]
            return v.upper()
        except KeyError:
            return "INFO"

    @property
    def data_dir_path(self) -> Path:
        """Get data directory as Path object (ensures directory exists)."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir

    @property
    def db_path(self) -> Path:
        """Get database file path."""
        db_path = self.data_dir_path / "database" / "vacuumarr.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path

    @property
    def log_level_enum(self) -> LogLevel:
        """Get log level as enum."""
        try:
            return LogLevel[self.log_level]
        except KeyError:
            return LogLevel.INFO

    @property
    def log_dir(self) -> Path:
        """Get log directory path."""
        log_path = self.data_dir_path / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list."""
        if not self.cors_origins or self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def version(self) -> str:
        """Get application version."""
        return str(__version__)


# global settings instance
settings = Settings()
