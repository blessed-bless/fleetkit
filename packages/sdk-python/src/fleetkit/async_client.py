from __future__ import annotations

import socket
from typing import Any

import httpx

from fleetkit.client import FleetKitError


class AsyncFleetKit:
    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        api_key: str,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-FleetKit-Key": api_key},
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncFleetKit:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            raise FleetKitError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        if not resp.content or resp.text in {"null", ""}:
            return None
        return resp.json()

    async def register_worker(
        self,
        *,
        app_id: str,
        name: str,
        hostname: str | None = None,
        labels: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/agent/apps/{app_id}/workers/register",
            json={
                "name": name,
                "hostname": hostname or socket.gethostname(),
                "labels": labels or {},
                "meta": meta or {},
            },
        )

    async def heartbeat(
        self, worker_id: str, *, status: str = "online", meta: dict | None = None
    ) -> dict:
        return await self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/heartbeat",
            json={"status": status, "meta": meta or {}},
        )

    async def enqueue(
        self,
        *,
        app_id: str,
        name: str,
        payload: dict | None = None,
        queue: str = "default",
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/agent/apps/{app_id}/jobs",
            json={"name": name, "payload": payload or {}, "queue": queue},
        )

    async def claim(
        self, worker_id: str, queues: list[str] | None = None
    ) -> dict[str, Any] | None:
        params = [("queue", q) for q in (queues or [])]
        return await self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/claim",
            params=params,
        )

    async def complete(self, job_id: str, result: dict | None = None) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/complete",
            json={"result": result or {}},
        )

    async def fail(self, job_id: str, error: str, *, retry: bool = True) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/fail",
            json={"error": error, "retry": retry},
        )

    async def log_line(self, job_id: str, line: str, *, stream: str = "stdout") -> dict:
        return await self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/logs",
            json={"line": line, "stream": stream},
        )

    async def log_batch(self, job_id: str, lines: list[str], *, stream: str = "stdout") -> dict:
        return await self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/logs/batch",
            json={"lines": lines, "stream": stream},
        )

    async def metric(
        self,
        name: str,
        value: float,
        *,
        app_id: str | None = None,
        labels: dict | None = None,
    ) -> dict:
        return await self._request(
            "POST",
            "/api/v1/agent/metrics",
            json={"name": name, "value": value, "app_id": app_id, "labels": labels or {}},
        )
