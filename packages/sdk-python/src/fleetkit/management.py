from __future__ import annotations

from typing import Any

import httpx

from fleetkit.client import FleetKitError


class ManagementClient:
    """JWT control-plane client (dashboard / CLI style)."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        token: str,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ManagementClient:
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

    @classmethod
    def login(
        cls,
        email: str,
        password: str,
        *,
        base_url: str = "http://localhost:8000",
    ) -> tuple[ManagementClient, str]:
        with httpx.Client(base_url=base_url.rstrip("/"), timeout=30) as http:
            resp = http.post("/api/v1/auth/login", json={"email": email, "password": password})
            if resp.status_code >= 400:
                raise FleetKitError(f"login failed: {resp.status_code} {resp.text}")
            token = resp.json()["access_token"]
        return cls(base_url=base_url, token=token), token

    def overview(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/overview")

    def projects(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/projects")

    def create_project(self, *, name: str, slug: str, description: str = "") -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/projects",
            json={"name": name, "slug": slug, "description": description},
        )

    def apps(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/apps")

    def create_app(
        self, project_id: str, *, name: str, slug: str, kind: str = "worker"
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/apps",
            json={"name": name, "slug": slug, "kind": kind},
        )

    def jobs(
        self,
        project_id: str,
        *,
        status: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if tag:
            params["tag"] = tag
        if q:
            params["q"] = q
        return self._request("GET", f"/api/v1/projects/{project_id}/jobs", params=params)

    def enqueue(
        self,
        project_id: str,
        app_id: str,
        *,
        name: str,
        payload: dict | None = None,
        tags: list[str] | None = None,
        queue: str = "default",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/apps/{app_id}/jobs",
            json={
                "name": name,
                "payload": payload or {},
                "tags": tags or [],
                "queue": queue,
            },
        )

    def cancel_job(self, project_id: str, job_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/projects/{project_id}/jobs/{job_id}/cancel")

    def retry_job(self, project_id: str, job_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/projects/{project_id}/jobs/{job_id}/retry")

    def workers(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/workers")

    def drain_worker(self, project_id: str, worker_id: str, *, draining: bool = True) -> dict:
        return self._request(
            "POST",
            f"/api/v1/projects/{project_id}/workers/{worker_id}/drain",
            json={"draining": draining},
        )

    def schedules(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/schedules")

    def webhooks(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/webhooks")

    def health_checks(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/health-checks")

    def run_health_check(self, project_id: str, check_id: str) -> dict[str, Any]:
        return self._request(
            "POST", f"/api/v1/projects/{project_id}/health-checks/{check_id}/run"
        )

    def templates(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/templates")

    def run_template(self, project_id: str, template_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/projects/{project_id}/templates/{template_id}/run")

    def quotas(self, project_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/projects/{project_id}/quotas")

    def export_project(self, project_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/projects/{project_id}/export")

    def secrets(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/secrets")

    def dead_letters(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/api/v1/projects/{project_id}/dead-letters")

    def requeue(self, project_id: str, dlq_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/v1/projects/{project_id}/dead-letters/{dlq_id}/requeue")
