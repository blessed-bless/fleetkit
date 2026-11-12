"""Redact secrets from logs, events and audit payloads."""

from __future__ import annotations

import re
from typing import Any

_SECRET_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "access_token",
    "refresh_token",
    "private_key",
    "bot_token",
    "x-fleetkit-key",
    "x-fleetkit-signature",
}

_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-_\.=]+"),
    re.compile(r"fk_[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"),
]


def redact_text(text: str) -> str:
    out = text
    for pattern in _PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def _key_sensitive(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return lowered in _SECRET_KEYS or any(part in lowered for part in ("secret", "token", "password", "passwd"))


def redact_mapping(data: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return "[TRUNCATED]"
    if isinstance(data, dict):
        out = {}
        for key, value in data.items():
            if _key_sensitive(str(key)):
                out[key] = "[REDACTED]"
            else:
                out[key] = redact_mapping(value, depth=depth + 1)
        return out
    if isinstance(data, list):
        return [redact_mapping(item, depth=depth + 1) for item in data[:200]]
    if isinstance(data, str):
        return redact_text(data)
    return data
