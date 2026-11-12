"""Seed a demo app + API key + ping job via HTTP.

Usage:
  set FLEETKIT_EMAIL / FLEETKIT_PASSWORD (optional)
  python scripts/bootstrap_demo.py
"""

from __future__ import annotations

import os
import sys

import httpx

BASE = os.getenv("FLEETKIT_API_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.getenv("FLEETKIT_EMAIL", "admin@example.com")
PASSWORD = os.getenv("FLEETKIT_PASSWORD", "fleetkit-admin")


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=30) as client:
        health = client.get("/healthz")
        health.raise_for_status()
        token = client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        token.raise_for_status()
        headers = {"Authorization": f"Bearer {token.json()['access_token']}"}

        projects = client.get("/api/v1/projects", headers=headers)
        projects.raise_for_status()
        project = projects.json()[0]

        apps = client.get(f"/api/v1/projects/{project['id']}/apps", headers=headers)
        apps.raise_for_status()
        existing = [a for a in apps.json() if a["slug"] == "demo-worker"]
        if existing:
            app = existing[0]
        else:
            created = client.post(
                f"/api/v1/projects/{project['id']}/apps",
                headers=headers,
                json={"name": "Demo Worker", "slug": "demo-worker", "kind": "worker"},
            )
            created.raise_for_status()
            app = created.json()

        key = client.post(
            f"/api/v1/projects/{project['id']}/api-keys",
            headers=headers,
            json={"name": "demo-key"},
        )
        key.raise_for_status()
        secret = key.json()["secret"]

        job = client.post(
            f"/api/v1/projects/{project['id']}/apps/{app['id']}/jobs",
            headers=headers,
            json={"name": "ping", "payload": {"hello": "fleetkit"}},
        )
        job.raise_for_status()

        print("project:", project["id"])
        print("app_id:", app["id"])
        print("api_key:", secret)
        print("job_id:", job.json()["id"])
        print("\nExport:")
        print(f"set FLEETKIT_API_KEY={secret}")
        print(f"set FLEETKIT_APP_ID={app['id']}")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"bootstrap failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
