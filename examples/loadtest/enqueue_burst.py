"""Burst-enqueue helper for local load experiments.

Usage:
  set FLEETKIT_TOKEN=...
  set FLEETKIT_PROJECT_ID=...
  set FLEETKIT_APP_ID=...
  python enqueue_burst.py --count 100 --name ping
"""

from __future__ import annotations

import argparse
import os
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--name", default="ping")
    parser.add_argument("--base-url", default=os.getenv("FLEETKIT_API_URL", "http://localhost:8000"))
    args = parser.parse_args()

    token = os.environ["FLEETKIT_TOKEN"]
    project_id = os.environ["FLEETKIT_PROJECT_ID"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    headers = {"Authorization": f"Bearer {token}"}

    started = time.perf_counter()
    ok = 0
    with httpx.Client(base_url=args.base_url.rstrip("/"), headers=headers, timeout=30) as client:
        payloads = [{"i": i, "source": "loadtest"} for i in range(args.count)]
        # prefer batch endpoint when available
        resp = client.post(
            f"/api/v1/projects/{project_id}/jobs/batch",
            json={"app_id": app_id, "name": args.name, "payloads": payloads},
        )
        if resp.status_code < 300:
            ok = resp.json().get("count", 0)
        else:
            for i, payload in enumerate(payloads):
                r = client.post(
                    f"/api/v1/projects/{project_id}/apps/{app_id}/jobs",
                    json={"name": args.name, "payload": payload},
                )
                if r.status_code < 300:
                    ok += 1
                if i and i % 25 == 0:
                    print(f"progress {i}/{args.count}")
    elapsed = time.perf_counter() - started
    print(f"enqueued={ok} elapsed={elapsed:.2f}s rate={ok / max(elapsed, 0.001):.1f}/s")


if __name__ == "__main__":
    main()
