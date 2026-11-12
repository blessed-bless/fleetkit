from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
