"""Reusable payload parsers/helpers for worker jobs."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)


def require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"payload.{key} must be a non-empty string")
    return value.strip()


def require_url(payload: dict[str, Any], key: str = "url") -> str:
    url = require_str(payload, key)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"payload.{key} must be http(s) URL")
    return url


def as_int(payload: dict[str, Any], key: str, default: int, *, min_v: int | None = None, max_v: int | None = None) -> int:
    raw = payload.get(key, default)
    value = int(raw)
    if min_v is not None and value < min_v:
        value = min_v
    if max_v is not None and value > max_v:
        value = max_v
    return value


def as_float(payload: dict[str, Any], key: str, default: float, *, min_v: float | None = None, max_v: float | None = None) -> float:
    raw = payload.get(key, default)
    value = float(raw)
    if min_v is not None and value < min_v:
        value = min_v
    if max_v is not None and value > max_v:
        value = max_v
    return value


def extract_emails(text: str) -> list[str]:
    return sorted(set(EMAIL_RE.findall(text or "")))


def extract_urls(text: str) -> list[str]:
    return sorted(set(URL_RE.findall(text or "")))


def deep_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(flatten(value, full))
        else:
            out[full] = value
    return out


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    size = max(1, size)
    return [items[i : i + size] for i in range(0, len(items), size)]
