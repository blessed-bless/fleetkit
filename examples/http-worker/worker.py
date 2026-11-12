"""External worker using FleetKit SDK run_loop (claim-batch + heartbeats).

Env:
  FLEETKIT_API_URL   default http://localhost:8000
  FLEETKIT_API_KEY   project API key
  FLEETKIT_APP_ID    target app id
  FLEETKIT_BATCH     claim batch size (default 5)
  FLEETKIT_CONCURRENCY  parallel handlers (default 2)
"""

from __future__ import annotations

import os

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
        return {"pong": True, "tags": job.get("tags") or []}
    return {"ok": True, "echo": payload}


def main() -> None:
    api_key = os.environ["FLEETKIT_API_KEY"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    base_url = os.getenv("FLEETKIT_API_URL", "http://localhost:8000")
    batch = int(os.getenv("FLEETKIT_BATCH", "5"))
    concurrency = int(os.getenv("FLEETKIT_CONCURRENCY", "2"))

    with FleetKit(base_url=base_url, api_key=api_key) as fk:
        print(f"worker loop app={app_id} batch={batch} concurrency={concurrency}")
        fk.run_loop(
            app_id=app_id,
            worker_name=os.getenv("FLEETKIT_WORKER_NAME", "http-worker"),
            handler=handle,
            batch_size=batch,
            concurrency=concurrency,
            labels={"capability": os.getenv("FLEETKIT_CAPABILITY", "http")},
        )


if __name__ == "__main__":
    main()
