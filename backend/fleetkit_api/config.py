from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRETS = {
    "dev-insecure-secret-change-me",
    "change-me-to-a-long-random-string",
    "docker-dev-secret-change-in-production",
}
_INSECURE_BOOTSTRAP_PASSWORDS = {
    "fleetkit-admin",
    "admin",
    "password",
    "changeme",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLEETKIT_", env_file=".env", extra="ignore")

    env: str = "development"
    secret_key: str = "dev-insecure-secret-change-me"
    # Prefer Postgres in Docker; SQLite works for solo local smoke tests.
    database_url: str = "sqlite+aiosqlite:///./fleetkit.dev.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    bootstrap_email: str = "admin@example.com"
    bootstrap_password: str = "fleetkit-admin"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    access_token_minutes: int = 60 * 12
    worker_stale_seconds: int = 90
    job_default_timeout_seconds: int = 300
    project_name: str = Field(default="FleetKit")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_dev(self) -> bool:
        return self.env.lower() in {"dev", "development", "local"}

    @model_validator(mode="after")
    def reject_insecure_production(self) -> Settings:
        if self.is_dev:
            return self
        if self.secret_key in _INSECURE_SECRETS or len(self.secret_key) < 32:
            raise ValueError(
                "FLEETKIT_SECRET_KEY must be a unique string of at least 32 chars in production"
            )
        if self.bootstrap_password in _INSECURE_BOOTSTRAP_PASSWORDS:
            raise ValueError(
                "FLEETKIT_BOOTSTRAP_PASSWORD must not use the default demo password in production"
            )
        if self.database_url.startswith("sqlite"):
            raise ValueError("SQLite is not allowed when FLEETKIT_ENV=production — use Postgres")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
