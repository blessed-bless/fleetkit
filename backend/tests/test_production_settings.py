import os

import pytest
from pydantic import ValidationError


def test_production_rejects_default_secret(monkeypatch):
    monkeypatch.setenv("FLEETKIT_ENV", "production")
    monkeypatch.setenv("FLEETKIT_SECRET_KEY", "dev-insecure-secret-change-me")
    monkeypatch.setenv("FLEETKIT_BOOTSTRAP_PASSWORD", "not-the-demo-password")
    monkeypatch.setenv(
        "FLEETKIT_DATABASE_URL",
        "postgresql+asyncpg://fleetkit:fleetkit@localhost:5432/fleetkit",
    )
    from fleetkit_api.config import Settings

    with pytest.raises(ValidationError, match="FLEETKIT_SECRET_KEY"):
        Settings()


def test_production_rejects_sqlite(monkeypatch):
    monkeypatch.setenv("FLEETKIT_ENV", "production")
    monkeypatch.setenv("FLEETKIT_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("FLEETKIT_BOOTSTRAP_PASSWORD", "strong-admin-pass")
    monkeypatch.setenv("FLEETKIT_DATABASE_URL", "sqlite+aiosqlite:///./nope.db")
    from fleetkit_api.config import Settings

    with pytest.raises(ValidationError, match="SQLite"):
        Settings()


def test_production_accepts_strong_config(monkeypatch):
    monkeypatch.setenv("FLEETKIT_ENV", "production")
    monkeypatch.setenv("FLEETKIT_SECRET_KEY", "prod-secret-key-with-enough-length")
    monkeypatch.setenv("FLEETKIT_BOOTSTRAP_PASSWORD", "strong-admin-pass")
    monkeypatch.setenv(
        "FLEETKIT_DATABASE_URL",
        "postgresql+asyncpg://fleetkit:fleetkit@localhost:5432/fleetkit",
    )
    from fleetkit_api.config import Settings

    settings = Settings()
    assert not settings.is_dev
    assert len(settings.secret_key) >= 32


def test_dev_still_allows_defaults(monkeypatch):
    for key in list(os.environ):
        if key.startswith("FLEETKIT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("FLEETKIT_ENV", "development")
    from fleetkit_api.config import Settings

    settings = Settings()
    assert settings.is_dev
