"""Application configuration."""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Kloppy API"
    api_prefix: str = "/api"
    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"
    supabase_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_PROJECT_URL", "SUPABASE_URL"),
    )
    supabase_publishable_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SUPABASE_ANON_KEY",
            "SUPABASE_PUBLISHABLE_KEY",
        ),
    )
    memwal_url: str | None = None
    memwal_api_key: str | None = None
    strands_model_id: str | None = None
    websocket_path: str = "/api/assistant/ws"

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
