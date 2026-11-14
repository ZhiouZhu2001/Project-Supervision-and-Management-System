from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration read from the environment, never from code."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_version: str = "0.1.0"
    app_base_url: str = "http://localhost:8080"
    app_secret_key: str = "dev-only-not-a-secret"
    database_url: str = "postgresql+asyncpg://app:app@db:5432/supervision"


@lru_cache
def get_settings() -> Settings:
    return Settings()
