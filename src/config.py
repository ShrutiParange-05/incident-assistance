"""
Centralized application configuration.

All environment-driven values live here so the rest of the codebase
never touches os.environ directly. Copy .env.example to .env and fill
in real values before running the app.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql://incident_user:incident_pass@localhost:5432/incident_db"

    # GenAI
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    log_file: str = "logs/app.log"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-parsing .env on every import."""
    return Settings()
