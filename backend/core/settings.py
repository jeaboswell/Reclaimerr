from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # jellyfin
    jellyfin_url: str = ""
    jellyfin_api_key: str = ""

    # plex
    plex_url: str = ""
    plex_token: str = ""

    # radarr (optional)
    radarr_url: str = "http://localhost:7878"
    radarr_api_key: str = ""

    # sonarr (optional)
    sonarr_url: str = "http://localhost:8989"
    sonarr_api_key: str = ""

    # api configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = ""  # comma-separated list

    # deletion thresholds
    default_threshold_days: int = 180
    never_watched_threshold_days: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list."""
        if not self.cors_origins:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# global settings instance
settings = Settings()
