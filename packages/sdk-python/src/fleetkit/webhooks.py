from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any


def sign_payload(secret: str, body: bytes, *, timestamp: int | None = None) -> str:
    """HMAC-SHA256 hex digest: `{ts}.{body}`."""
    ts = int(time.time() if timestamp is None else timestamp)
    msg = f"{ts}.".encode() + body
    digest = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def verify_signature(
    secret: str,
    body: bytes,
    header: str,
    *,
    max_age_seconds: int = 300,
    now: int | None = None,
) -> bool:
    """Validate FleetKit-style webhook signature header `t=...,v1=...`."""
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    ts_raw = parts.get("t")
    sig = parts.get("v1")
    if not ts_raw or not sig:
        return False
    try:
        ts = int(ts_raw)
    except ValueError:
        return False
    clock = int(time.time() if now is None else now)
    if abs(clock - ts) > max_age_seconds:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def build_ingest_url(base_url: str, path_token: str) -> str:
    return f"{base_url.rstrip('/')}/api/v1/hooks/{path_token}"


def parse_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize inbound webhook JSON into job-friendly fields."""
    return {
        "event": payload.get("event") or payload.get("type") or "webhook",
        "source": payload.get("source") or "external",
        "data": payload.get("data") if isinstance(payload.get("data"), dict) else payload,
    }
