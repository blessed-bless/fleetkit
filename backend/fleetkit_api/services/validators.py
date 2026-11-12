from __future__ import annotations

import re
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
FLAG_KEY_RE = re.compile(r"^[a-z0-9_\.\-]+$")
CRON_FIELDS = 5


def validate_slug(value: str, *, field: str = "slug") -> str:
    if not SLUG_RE.match(value):
        raise ValueError(f"{field} must match {SLUG_RE.pattern}")
    if len(value) > 64:
        raise ValueError(f"{field} too long")
    return value


def validate_cron(expr: str) -> str:
    parts = expr.split()
    if len(parts) not in {5, 6}:
        raise ValueError("cron must have 5 or 6 fields")
    return expr


def validate_env_key(key: str) -> str:
    if not ENV_KEY_RE.match(key):
        raise ValueError("env key must look like FOO_BAR")
    return key


def validate_flag_key(key: str) -> str:
    if not FLAG_KEY_RE.match(key):
        raise ValueError("flag key invalid")
    return key


def validate_priority(value: int) -> int:
    if value < 0 or value > 100:
        raise ValueError("priority must be 0..100")
    return value


def validate_timeout(seconds: int) -> int:
    if seconds < 5 or seconds > 86400:
        raise ValueError("timeout_seconds out of range")
    return seconds


def sanitize_labels(labels: dict[str, Any] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in (labels or {}).items():
        k = str(key)[:64]
        out[k] = str(value)[:256]
    return out


def truncate(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"
