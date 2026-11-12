from __future__ import annotations

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

import httpx


class FleetKitError(RuntimeError):
    pass


class FleetKit:
    """HTTP client for the FleetKit agent API (API key)."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        api_key: str,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-FleetKit-Key": api_key},
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> FleetKit:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = self._client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            raise FleetKitError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        if not resp.content or resp.text in {"null", ""}:
            return None
        return resp.json()

    def register_worker(
        self,
        *,
        app_id: str,
        name: str,
        hostname: str | None = None,
        labels: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/agent/apps/{app_id}/workers/register",
            json={
                "name": name,
                "hostname": hostname or socket.gethostname(),
                "labels": labels or {},
                "meta": meta or {},
            },
        )

    def heartbeat(
        self, worker_id: str, *, status: str = "online", meta: dict | None = None
    ) -> dict:
        return self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/heartbeat",
            json={"status": status, "meta": meta or {}},
        )

    def drain(self, worker_id: str, *, draining: bool = True) -> dict:
        status = "draining" if draining else "online"
        return self.heartbeat(worker_id, status=status, meta={"drain": draining})

    def enqueue(
        self,
        *,
        app_id: str,
        name: str,
        payload: dict | None = None,
        queue: str = "default",
        tags: list[str] | None = None,
        max_attempts: int = 3,
        timeout_seconds: int = 300,
        priority: int | None = None,
        depends_on_job_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "name": name,
            "payload": payload or {},
            "queue": queue,
            "tags": tags or [],
            "max_attempts": max_attempts,
            "timeout_seconds": timeout_seconds,
        }
        if priority is not None:
            body["priority"] = priority
        if depends_on_job_id is not None:
            body["depends_on_job_id"] = depends_on_job_id
        return self._request("POST", f"/api/v1/agent/apps/{app_id}/jobs", json=body)

    def claim(self, worker_id: str, queues: list[str] | None = None) -> dict[str, Any] | None:
        params = [("queue", q) for q in (queues or [])]
        return self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/claim",
            params=params,
        )

    def claim_batch(
        self,
        worker_id: str,
        *,
        queues: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        params: list[tuple[str, str | int]] = [("limit", limit)]
        for q in queues or []:
            params.append(("queue", q))
        rows = self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/claim-batch",
            params=params,
        )
        return list(rows or [])

    def complete(self, job_id: str, result: dict | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/complete",
            json={"result": result or {}},
        )

    def fail(self, job_id: str, error: str, *, retry: bool = True) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/fail",
            json={"error": error, "retry": retry},
        )

    def log_line(self, job_id: str, line: str, *, stream: str = "stdout") -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/logs",
            json={"line": line, "stream": stream},
        )

    def log_batch(
        self, job_id: str, lines: list[str], *, stream: str = "stdout"
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/agent/jobs/{job_id}/logs/batch",
            json={"lines": lines, "stream": stream},
        )

    def metric(
        self,
        name: str,
        value: float,
        *,
        app_id: str | None = None,
        labels: dict | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/agent/metrics",
            json={
                "name": name,
                "value": value,
                "app_id": app_id,
                "labels": labels or {},
            },
        )

    def _handle_job(self, handler: Callable[[dict], Any], job: dict[str, Any]) -> None:
        try:
            self.log_line(job["id"], f"start {job['name']}")
            result = handler(job)
            self.complete(job["id"], result if isinstance(result, dict) else {"result": result})
        except Exception as exc:  # noqa: BLE001
            self.fail(job["id"], str(exc), retry=True)

    def run_loop(
        self,
        *,
        app_id: str,
        worker_name: str,
        handler: Callable[[dict], Any],
        poll_interval: float = 1.5,
        queues: list[str] | None = None,
        batch_size: int = 1,
        concurrency: int = 1,
        heartbeat_interval: float = 15.0,
        labels: dict[str, Any] | None = None,
        max_jobs: int | None = None,
    ) -> None:
        """Blocking poll loop with optional claim-batch and thread pool."""
        worker = self.register_worker(app_id=app_id, name=worker_name, labels=labels)
        worker_id = worker["id"]
        stop = threading.Event()
        processed = 0

        def _heartbeat() -> None:
            while not stop.wait(heartbeat_interval):
                try:
                    self.heartbeat(worker_id)
                except Exception:  # noqa: BLE001
                    pass

        hb = threading.Thread(target=_heartbeat, name="fleetkit-hb", daemon=True)
        hb.start()

        pool = ThreadPoolExecutor(max_workers=max(1, concurrency)) if concurrency > 1 else None
        try:
            while True:
                if max_jobs is not None and processed >= max_jobs:
                    break
                if batch_size > 1:
                    jobs = self.claim_batch(worker_id, queues=queues, limit=batch_size)
                else:
                    one = self.claim(worker_id, queues=queues)
                    jobs = [one] if one else []
                if not jobs:
                    time.sleep(poll_interval)
                    continue
                if pool is None:
                    for job in jobs:
                        self._handle_job(handler, job)
                        processed += 1
                        if max_jobs is not None and processed >= max_jobs:
                            break
                else:
                    futs = [pool.submit(self._handle_job, handler, job) for job in jobs]
                    for fut in as_completed(futs):
                        fut.result()
                        processed += 1
        finally:
            stop.set()
            if pool is not None:
                pool.shutdown(wait=True, cancel_futures=False)
            try:
                self.drain(worker_id, draining=True)
            except Exception:  # noqa: BLE001
                pass
