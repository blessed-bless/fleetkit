from __future__ import annotations

import asyncio
import socket
from typing import Any, Awaitable, Callable

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

    async def drain(self, worker_id: str, *, draining: bool = True) -> dict:
        status = "draining" if draining else "online"
        return await self.heartbeat(worker_id, status=status, meta={"drain": draining})

    async def enqueue(
        self,
        *,
        app_id: str,
        name: str,
        payload: dict | None = None,
        queue: str = "default",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/agent/apps/{app_id}/jobs",
            json={
                "name": name,
                "payload": payload or {},
                "queue": queue,
                "tags": tags or [],
            },
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

    async def claim_batch(
        self,
        worker_id: str,
        *,
        queues: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        params: list[tuple[str, str | int]] = [("limit", limit)]
        for q in queues or []:
            params.append(("queue", q))
        rows = await self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/claim-batch",
            params=params,
        )
        return list(rows or [])

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

    async def _handle_job(
        self, handler: Callable[[dict], Awaitable[Any] | Any], job: dict[str, Any]
    ) -> None:
        try:
            await self.log_line(job["id"], f"start {job['name']}")
            result = handler(job)
            if asyncio.iscoroutine(result):
                result = await result
            await self.complete(
                job["id"], result if isinstance(result, dict) else {"result": result}
            )
        except Exception as exc:  # noqa: BLE001
            await self.fail(job["id"], str(exc), retry=True)

    async def run_loop(
        self,
        *,
        app_id: str,
        worker_name: str,
        handler: Callable[[dict], Awaitable[Any] | Any],
        poll_interval: float = 1.5,
        queues: list[str] | None = None,
        batch_size: int = 1,
        concurrency: int = 1,
        heartbeat_interval: float = 15.0,
        labels: dict[str, Any] | None = None,
        max_jobs: int | None = None,
    ) -> None:
        worker = await self.register_worker(app_id=app_id, name=worker_name, labels=labels)
        worker_id = worker["id"]
        processed = 0
        stop = asyncio.Event()

        async def _heartbeat() -> None:
            while not stop.is_set():
                try:
                    await self.heartbeat(worker_id)
                except Exception:  # noqa: BLE001
                    pass
                try:
                    await asyncio.wait_for(stop.wait(), timeout=heartbeat_interval)
                except asyncio.TimeoutError:
                    continue

        hb_task = asyncio.create_task(_heartbeat())
        sem = asyncio.Semaphore(max(1, concurrency))
        try:
            while True:
                if max_jobs is not None and processed >= max_jobs:
                    break
                if batch_size > 1:
                    jobs = await self.claim_batch(worker_id, queues=queues, limit=batch_size)
                else:
                    one = await self.claim(worker_id, queues=queues)
                    jobs = [one] if one else []
                if not jobs:
                    await asyncio.sleep(poll_interval)
                    continue

                async def _run(job: dict[str, Any]) -> None:
                    async with sem:
                        await self._handle_job(handler, job)

                await asyncio.gather(*[_run(j) for j in jobs])
                processed += len(jobs)
        finally:
            stop.set()
            hb_task.cancel()
            try:
                await self.drain(worker_id, draining=True)
            except Exception:  # noqa: BLE001
                pass
