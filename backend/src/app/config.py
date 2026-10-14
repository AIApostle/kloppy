"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Kloppy API"
    api_prefix: str = "/api"
    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    memwal_url: str | None = None
    memwal_api_key: str | None = None
    strands_model_id: str = "kloppy-balanced"
    websocket_path: str = "/api/assistant/ws"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
