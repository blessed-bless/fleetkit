from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import Any

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s fleetkit.worker | %(message)s",
)
logger = logging.getLogger("fleetkit.worker")


class FleetWorker:
    def __init__(self) -> None:
        self.base_url = os.getenv("FLEETKIT_API_URL", "http://api:8000").rstrip("/")
        self.api_key = os.getenv("FLEETKIT_API_KEY", "")
        self.app_id = os.getenv("FLEETKIT_APP_ID", "")
        self.worker_name = os.getenv("FLEETKIT_WORKER_NAME", f"worker-{socket.gethostname()}")
        self.poll_interval = float(os.getenv("FLEETKIT_POLL_INTERVAL", "2"))
        self.worker_id: str | None = None

    @property
    def headers(self) -> dict[str, str]:
        return {"X-FleetKit-Key": self.api_key, "Content-Type": "application/json"}

    async def register(self, client: httpx.AsyncClient) -> None:
        if not self.api_key or not self.app_id:
            logger.warning(
                "FLEETKIT_API_KEY / FLEETKIT_APP_ID not set — worker idle. "
                "Create an app + API key in the dashboard, then restart."
            )
            return
        resp = await client.post(
            f"{self.base_url}/api/v1/agent/apps/{self.app_id}/workers/register",
            headers=self.headers,
            json={
                "name": self.worker_name,
                "hostname": socket.gethostname(),
                "labels": {"runtime": "fleetkit-worker"},
                "meta": {"pid": os.getpid()},
            },
        )
        resp.raise_for_status()
        self.worker_id = resp.json()["id"]
        logger.info("Registered worker_id=%s name=%s", self.worker_id, self.worker_name)

    async def heartbeat(self, client: httpx.AsyncClient) -> None:
        if not self.worker_id:
            return
        await client.post(
            f"{self.base_url}/api/v1/agent/workers/{self.worker_id}/heartbeat",
            headers=self.headers,
            json={"status": "online", "meta": {}},
            timeout=10,
        )

    async def handle_job(self, job: dict[str, Any]) -> dict[str, Any]:
        import fleetkit_worker.builtin_jobs  # noqa: F401
        import fleetkit_worker.net_jobs  # noqa: F401
        import fleetkit_worker.text_jobs  # noqa: F401
        from fleetkit_worker.handlers import get_handler

        name = job.get("name", "")
        payload = job.get("payload") or {}
        logger.info("Running job %s (%s)", job.get("id"), name)
        handler = get_handler(name)
        if handler is None:
            return {"ok": True, "echo": payload, "job_name": name}
        return await handler(payload)

    async def claim_and_run(self, client: httpx.AsyncClient) -> bool:
        if not self.worker_id:
            return False
        resp = await client.post(
            f"{self.base_url}/api/v1/agent/workers/{self.worker_id}/claim",
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content or resp.text in {"null", ""}:
            return False
        job = resp.json()
        if not job:
            return False
        try:
            result = await self.handle_job(job)
            await client.post(
                f"{self.base_url}/api/v1/agent/jobs/{job['id']}/complete",
                headers=self.headers,
                json={"result": result},
            )
        except Exception as exc:
            logger.exception("Job %s crashed", job.get("id"))
            await client.post(
                f"{self.base_url}/api/v1/agent/jobs/{job['id']}/fail",
                headers=self.headers,
                json={"error": str(exc), "retry": True},
            )
        return True

    async def run_forever(self) -> None:
        async with httpx.AsyncClient() as client:
            # wait for API
            for _attempt in range(60):
                try:
                    health = await client.get(f"{self.base_url}/healthz", timeout=3)
                    if health.status_code == 200:
                        break
                except httpx.HTTPError:
                    logger.debug("API not ready yet at %s", self.base_url)
                await asyncio.sleep(1)
            else:
                logger.error("API at %s never became healthy", self.base_url)
                return

            await self.register(client)
            ticks = 0
            while True:
                try:
                    if self.worker_id:
                        worked = await self.claim_and_run(client)
                        ticks += 1
                        if ticks % 15 == 0:
                            await self.heartbeat(client)
                        if not worked:
                            await asyncio.sleep(self.poll_interval)
                    else:
                        await asyncio.sleep(10)
                        await self.register(client)
                except Exception:
                    logger.exception("Worker loop error")
                    await asyncio.sleep(3)


def main() -> None:
    asyncio.run(FleetWorker().run_forever())


if __name__ == "__main__":
    main()
