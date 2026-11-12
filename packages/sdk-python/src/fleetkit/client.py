from __future__ import annotations

import socket
from typing import Any

import httpx


class FleetKitError(RuntimeError):
    pass


class FleetKit:
    """Thin HTTP client for the FleetKit agent API."""

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

    def heartbeat(self, worker_id: str, *, status: str = "online", meta: dict | None = None) -> dict:
        return self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/heartbeat",
            json={"status": status, "meta": meta or {}},
        )

    def enqueue(
        self,
        *,
        app_id: str,
        name: str,
        payload: dict | None = None,
        queue: str = "default",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/agent/apps/{app_id}/jobs",
            json={"name": name, "payload": payload or {}, "queue": queue},
        )

    def claim(self, worker_id: str, queues: list[str] | None = None) -> dict[str, Any] | None:
        params = [("queue", q) for q in (queues or [])]
        return self._request(
            "POST",
            f"/api/v1/agent/workers/{worker_id}/claim",
            params=params,
        )

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

    def run_loop(
        self,
        *,
        app_id: str,
        worker_name: str,
        handler,
        poll_interval: float = 1.5,
        queues: list[str] | None = None,
    ) -> None:
        """Blocking poll loop. `handler(job) -> dict`."""
        import time

        worker = self.register_worker(app_id=app_id, name=worker_name)
        worker_id = worker["id"]
        while True:
            job = self.claim(worker_id, queues=queues)
            if not job:
                time.sleep(poll_interval)
                continue
            try:
                self.log_line(job["id"], f"start {job['name']}")
                result = handler(job)
                self.complete(job["id"], result if isinstance(result, dict) else {"result": result})
            except Exception as exc:  # noqa: BLE001
                self.fail(job["id"], str(exc), retry=True)

