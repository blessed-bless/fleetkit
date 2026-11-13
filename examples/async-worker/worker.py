"""Async worker using AsyncFleetKit.run_loop.

Env: FLEETKIT_API_KEY, FLEETKIT_APP_ID, optional FLEETKIT_API_URL.
"""

from __future__ import annotations

import asyncio
import os

from fleetkit import AsyncFleetKit


async def handle(job: dict) -> dict:
    await asyncio.sleep(0.05)
    if job["name"] == "ping":
        return {"pong": True, "async": True}
    return {"ok": True, "echo": job.get("payload") or {}}


async def main() -> None:
    api_key = os.environ["FLEETKIT_API_KEY"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    base_url = os.getenv("FLEETKIT_API_URL", "http://localhost:8000")
    async with AsyncFleetKit(base_url=base_url, api_key=api_key) as fk:
        await fk.run_loop(
            app_id=app_id,
            worker_name=os.getenv("FLEETKIT_WORKER_NAME", "async-worker"),
            handler=handle,
            batch_size=int(os.getenv("FLEETKIT_BATCH", "5")),
            concurrency=int(os.getenv("FLEETKIT_CONCURRENCY", "4")),
        )


if __name__ == "__main__":
    asyncio.run(main())
