from __future__ import annotations

import asyncio
import socket
from typing import Any

import httpx

from fleetkit_worker.handlers import job
from fleetkit_worker.parsers import as_float, as_int, require_str, require_url


@job("net.dns")
async def net_dns(payload: dict[str, Any]) -> dict[str, Any]:
    host = require_str(payload, "host")
    infos = await asyncio.to_thread(socket.getaddrinfo, host, None)
    addrs = sorted({item[4][0] for item in infos})
    return {"host": host, "addresses": addrs}


@job("net.tcp_check")
async def net_tcp_check(payload: dict[str, Any]) -> dict[str, Any]:
    host = require_str(payload, "host")
    port = as_int(payload, "port", 80, min_v=1, max_v=65535)
    timeout = as_float(payload, "timeout", 3.0, min_v=0.2, max_v=30.0)

    def _connect() -> bool:
        with socket.create_connection((host, port), timeout=timeout):
            return True

    try:
        await asyncio.to_thread(_connect)
        return {"ok": True, "host": host, "port": port}
    except OSError as exc:
        return {"ok": False, "host": host, "port": port, "error": str(exc)}


@job("net.http_status")
async def net_http_status(payload: dict[str, Any]) -> dict[str, Any]:
    url = require_url(payload)
    timeout = as_float(payload, "timeout", 10.0, min_v=1.0, max_v=60.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.head(url)
        if resp.status_code >= 400:
            resp = await client.get(url)
    return {
        "url": url,
        "status_code": resp.status_code,
        "final_url": str(resp.url),
        "elapsed_ms": resp.elapsed.total_seconds() * 1000,
    }


@job("net.multi_http")
async def net_multi_http(payload: dict[str, Any]) -> dict[str, Any]:
    urls = payload.get("urls") or []
    if not isinstance(urls, list) or not urls:
        raise ValueError("payload.urls must be a non-empty list")
    if len(urls) > 20:
        raise ValueError("max 20 urls")
    timeout = as_float(payload, "timeout", 10.0, min_v=1.0, max_v=30.0)
    results = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for url in urls:
            try:
                resp = await client.get(str(url))
                results.append({"url": url, "status_code": resp.status_code, "ok": True})
            except Exception as exc:  # noqa: BLE001
                results.append({"url": url, "ok": False, "error": str(exc)})
    return {"results": results, "ok_count": sum(1 for r in results if r.get("ok"))}


for _n in range(1, 16):
    def _factory(n: int = _n):
        @job(f"net.probe.{n:02d}")
        async def _handler(payload: dict[str, Any], idx: int = n) -> dict[str, Any]:
            host = str(payload.get("host", "example.com"))
            return {"probe": idx, "host": host, "note": "synthetic probe slot"}

        return _handler

    _factory()
