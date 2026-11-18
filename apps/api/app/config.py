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

    # Where uploaded images live. The proxy serves them from the same volume
    # through X-Accel-Redirect, so Python never streams a file body.
    upload_dir: str = "/data/uploads"

    # Outbound mail. Empty host means "not configured": the digest records the
    # attempt and fails loudly in the log rather than pretending to send.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_starttls: bool = True
    # Where the digest goes; falls back to the owner's address.
    alert_email: str = ""

    # In-process scheduler (invariant 8). Lets a one-off process opt out.
    scheduler_enabled: bool = True

    # The backup sidecar writes its verdict here; /healthz reads it, so a
    # silent backup failure is visible from outside.
    backup_status_file: str = "/data/backup-status/status.json"

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
