from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_SECRET = "dev-only-not-a-secret"
DEVELOPMENT_PASSWORD = "devpassword"


class Settings(BaseSettings):
    """Configuration read from the environment, never from code."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_version: str = "0.1.0"
    app_base_url: str = "http://localhost:8080"
    app_secret_key: str = DEVELOPMENT_SECRET
    database_url: str = "postgresql+asyncpg://app:devpassword@db:5432/supervision"

    # The single account, seeded on first boot. There is no registration.
    app_email: str = "owner@example.com"
    app_password: str = DEVELOPMENT_PASSWORD

    # Compose sets this to "1": migrations and seeding run during startup so
    # that `make dev` produces a working login on a clean clone. Tests leave
    # it unset and build the schema themselves.
    run_migrations: bool = False

    @property
    def cookie_secure(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
