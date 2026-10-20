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
    frontend_origins: str = "https://kloppy.vercel.app"
    environment: str = "production"
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
    qloo_api_key: str | None = None
    qloo_base_url: str = Field(
        default="https://api.qloo.com",
        validation_alias=AliasChoices("QLOO_API_URL", "QLOO_BASE_URL"),
    )
    mcp_servers_json: str | None = None
    integration_encryption_key: str | None = None
    strands_model_id: str = "openrouter/free"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str | None = None
    openrouter_app_title: str = "Kloppy"
    websocket_path: str = "/api/assistant/ws"

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
