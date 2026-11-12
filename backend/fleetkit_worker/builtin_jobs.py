"""Catalog of built-in job handlers used by the FleetKit worker runtime."""

from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from fleetkit_worker.handlers import job


@job("system.info")
async def system_info(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "payload": payload,
        "ts": datetime.now(UTC).isoformat(),
    }


@job("http.fetch")
async def http_fetch(payload: dict[str, Any]) -> dict[str, Any]:
    from fleetkit_api.security_suite.headers import sanitize_header_map
    from fleetkit_api.security_suite.ssrf import assert_safe_url

    url = assert_safe_url(str(payload["url"]), allow_private=bool(payload.get("allow_private")))
    method = payload.get("method", "GET").upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}:
        raise ValueError(f"method not allowed: {method}")
    headers = sanitize_header_map(payload.get("headers") or {})
    body = payload.get("body")
    timeout = min(60.0, max(1.0, float(payload.get("timeout", 20))))
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        resp = await client.request(method, url, headers=headers, content=body)
    text = resp.text
    return {
        "status_code": resp.status_code,
        "bytes": len(resp.content),
        "sha256": hashlib.sha256(resp.content).hexdigest(),
        "preview": text[:500],
        "headers": dict(resp.headers),
    }


@job("http.json")
async def http_json(payload: dict[str, Any]) -> dict[str, Any]:
    from fleetkit_api.security_suite.ssrf import assert_safe_url

    url = assert_safe_url(str(payload["url"]), allow_private=bool(payload.get("allow_private")))
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    return {"ok": True, "type": type(data).__name__, "keys": list(data)[:50] if isinstance(data, dict) else None}


@job("util.sleep")
async def util_sleep(payload: dict[str, Any]) -> dict[str, Any]:
    seconds = float(payload.get("seconds", 1))
    seconds = max(0.0, min(seconds, 60.0))
    started = time.perf_counter()
    import asyncio

    await asyncio.sleep(seconds)
    return {"slept": seconds, "elapsed": time.perf_counter() - started}


@job("util.hash")
async def util_hash(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text", "")
    algo = payload.get("algo", "sha256")
    h = hashlib.new(algo)
    h.update(str(text).encode("utf-8"))
    return {"algo": algo, "digest": h.hexdigest()}


@job("util.json.validate")
async def util_json_validate(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("raw")
    if isinstance(raw, (dict, list)):
        return {"ok": True, "parsed": True, "type": type(raw).__name__}
    parsed = json.loads(str(raw))
    return {"ok": True, "type": type(parsed).__name__}


@job("notify.echo")
async def notify_echo(payload: dict[str, Any]) -> dict[str, Any]:
    return {"echo": payload, "at": datetime.now(UTC).isoformat()}


@job("transform.map_keys")
async def transform_map_keys(payload: dict[str, Any]) -> dict[str, Any]:
    mapping = payload.get("mapping") or {}
    source = payload.get("data") or {}
    out = {}
    for src, dst in mapping.items():
        if src in source:
            out[dst] = source[src]
    return {"mapped": out}


@job("transform.filter_keys")
async def transform_filter_keys(payload: dict[str, Any]) -> dict[str, Any]:
    keys = set(payload.get("keys") or [])
    source = payload.get("data") or {}
    return {"filtered": {k: v for k, v in source.items() if k in keys}}


@job("batch.split")
async def batch_split(payload: dict[str, Any]) -> dict[str, Any]:
    items = list(payload.get("items") or [])
    size = max(1, int(payload.get("size", 10)))
    chunks = [items[i : i + size] for i in range(0, len(items), size)]
    return {"chunks": len(chunks), "sizes": [len(c) for c in chunks]}


@job("demo.fail")
async def demo_fail(payload: dict[str, Any]) -> dict[str, Any]:
    raise RuntimeError(payload.get("message") or "demo failure")


@job("demo.flaky")
async def demo_flaky(payload: dict[str, Any]) -> dict[str, Any]:
    # fails until attempt hint reaches threshold (caller can pass attempt)
    attempt = int(payload.get("attempt", 1))
    need = int(payload.get("succeed_after", 2))
    if attempt < need:
        raise RuntimeError(f"flaky until attempt {need}, now {attempt}")
    return {"ok": True, "attempt": attempt}


@job("telegram.send_text")
async def telegram_send_text(payload: dict[str, Any]) -> dict[str, Any]:
    token = payload["bot_token"]
    chat_id = payload["chat_id"]
    text = payload["text"]
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )
    return {"status_code": resp.status_code, "body": resp.json()}


@job("cron.heartbeat")
async def cron_heartbeat(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "schedule_id": payload.get("_schedule_id"),
        "ts": datetime.now(UTC).isoformat(),
    }
