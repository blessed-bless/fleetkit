"""Minimal external worker using the FleetKit Python SDK.

Env:
  FLEETKIT_API_URL   default http://localhost:8000
  FLEETKIT_API_KEY   project API key
  FLEETKIT_APP_ID    target app id
"""

from __future__ import annotations

import os
import time

from fleetkit import FleetKit


def handle(job: dict) -> dict:
    name = job["name"]
    payload = job.get("payload") or {}
    if name == "http.fetch":
        import httpx

        url = payload["url"]
        with httpx.Client(timeout=20) as client:
            resp = client.get(url)
        return {"status_code": resp.status_code, "bytes": len(resp.content), "url": url}
    if name == "ping":
        return {"pong": True}
    return {"ok": True, "echo": payload}


def main() -> None:
    api_key = os.environ["FLEETKIT_API_KEY"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    base_url = os.getenv("FLEETKIT_API_URL", "http://localhost:8000")

    with FleetKit(base_url=base_url, api_key=api_key) as fk:
        worker = fk.register_worker(app_id=app_id, name="http-worker")
        print(f"registered {worker['id']}")
        while True:
            job = fk.claim(worker["id"])
            if not job:
                time.sleep(1.5)
                continue
            try:
                result = handle(job)
                fk.complete(job["id"], result)
                print(f"done {job['id']} {job['name']}")
            except Exception as exc:
                fk.fail(job["id"], str(exc), retry=True)
                print(f"fail {job['id']}: {exc}")


if __name__ == "__main__":
    main()
