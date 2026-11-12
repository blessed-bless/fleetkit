from __future__ import annotations

from typing import Any

import httpx


class CliClient:
    def __init__(self, base_url: str, token: str | None = None, api_key: str | None = None) -> None:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if api_key:
            headers["X-FleetKit-Key"] = api_key
        self._http = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=30)

    def close(self) -> None:
        self._http.close()

    def login(self, email: str, password: str) -> str:
        resp = self._http.post("/api/v1/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        return resp.json()["access_token"]

    def overview(self) -> dict[str, Any]:
        resp = self._http.get("/api/v1/overview")
        resp.raise_for_status()
        return resp.json()

    def projects(self) -> list[dict[str, Any]]:
        resp = self._http.get("/api/v1/projects")
        resp.raise_for_status()
        return resp.json()

    def create_project(self, name: str, slug: str, description: str = "") -> dict[str, Any]:
        resp = self._http.post(
            "/api/v1/projects",
            json={"name": name, "slug": slug, "description": description},
        )
        resp.raise_for_status()
        return resp.json()

    def apps(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/apps")
        resp.raise_for_status()
        return resp.json()

    def enqueue(
        self,
        project_id: str,
        app_id: str,
        name: str,
        payload: dict | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        resp = self._http.post(
            f"/api/v1/projects/{project_id}/apps/{app_id}/jobs",
            json={"name": name, "payload": payload or {}, "tags": tags or []},
        )
        resp.raise_for_status()
        return resp.json()

    def jobs(
        self,
        project_id: str,
        *,
        status: str | None = None,
        tag: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if tag:
            params["tag"] = tag
        if q:
            params["q"] = q
        resp = self._http.get(f"/api/v1/projects/{project_id}/jobs", params=params)
        resp.raise_for_status()
        return resp.json()

    def cancel_job(self, project_id: str, job_id: str) -> dict[str, Any]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/jobs/{job_id}/cancel")
        resp.raise_for_status()
        return resp.json()

    def retry_job(self, project_id: str, job_id: str) -> dict[str, Any]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/jobs/{job_id}/retry")
        resp.raise_for_status()
        return resp.json()

    def workers(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/workers")
        resp.raise_for_status()
        return resp.json()

    def drain_worker(self, project_id: str, worker_id: str, draining: bool = True) -> dict:
        resp = self._http.post(
            f"/api/v1/projects/{project_id}/workers/{worker_id}/drain",
            json={"draining": draining},
        )
        resp.raise_for_status()
        return resp.json()

    def schedules(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/schedules")
        resp.raise_for_status()
        return resp.json()

    def webhooks(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/webhooks")
        resp.raise_for_status()
        return resp.json()

    def health_checks(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/health-checks")
        resp.raise_for_status()
        return resp.json()

    def run_health(self, project_id: str, check_id: str) -> dict[str, Any]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/health-checks/{check_id}/run")
        resp.raise_for_status()
        return resp.json()

    def templates(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/templates")
        resp.raise_for_status()
        return resp.json()

    def run_template(self, project_id: str, template_id: str) -> dict[str, Any]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/templates/{template_id}/run")
        resp.raise_for_status()
        return resp.json()

    def quotas(self, project_id: str) -> dict[str, Any]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/quotas")
        resp.raise_for_status()
        return resp.json()

    def export_project(self, project_id: str) -> dict[str, Any]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/export")
        resp.raise_for_status()
        return resp.json()

    def secrets(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/secrets")
        resp.raise_for_status()
        return resp.json()

    def search(self, project_id: str, q: str) -> dict[str, Any]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/search", params={"q": q})
        resp.raise_for_status()
        return resp.json()

    def dead_letters(self, project_id: str) -> list[dict[str, Any]]:
        resp = self._http.get(f"/api/v1/projects/{project_id}/dead-letters")
        resp.raise_for_status()
        return resp.json()

    def requeue(self, project_id: str, dlq_id: str) -> dict[str, Any]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/dead-letters/{dlq_id}/requeue")
        resp.raise_for_status()
        return resp.json()

    def evaluate_alerts(self, project_id: str) -> dict[str, Any]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/alerts/evaluate")
        resp.raise_for_status()
        return resp.json()

    def snapshot_metrics(self, project_id: str) -> dict[str, float]:
        resp = self._http.post(f"/api/v1/projects/{project_id}/metrics/snapshot")
        resp.raise_for_status()
        return resp.json()
