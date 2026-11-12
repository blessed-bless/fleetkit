from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fleetkit_api import __version__
from fleetkit_api.config import get_settings
from fleetkit_api.db import Base, SessionLocal, engine
from fleetkit_api.redis_client import ping_redis
from fleetkit_api.routers import apps, auth, jobs, overview, projects, schedules, webhooks, workers
from fleetkit_api.services.bootstrap import ensure_bootstrap_admin
from fleetkit_api.services.schedules import tick_schedules
from fleetkit_api.services.workers import mark_stale_workers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("fleetkit.api")


async def _scheduler_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            async with SessionLocal() as db:
                created = await tick_schedules(db)
                stale = await mark_stale_workers(db)
                await db.commit()
                if created:
                    logger.info("Scheduler enqueued %s job(s)", created)
                if stale:
                    logger.info("Marked %s worker(s) offline after missed heartbeat", stale)
        except Exception:
            logger.exception("Scheduler tick failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=15)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logger.info("FleetKit API %s starting (%s)", __version__, settings.env)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_bootstrap_admin()
    stop = asyncio.Event()
    task = asyncio.create_task(_scheduler_loop(stop))
    yield
    stop.set()
    await task
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FleetKit API",
        version=__version__,
        description="Control plane for bots, workers, schedules and webhooks",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(apps.router, prefix="/api/v1")
    app.include_router(workers.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(schedules.router, prefix="/api/v1")
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(overview.router, prefix="/api/v1")

    @app.get("/healthz")
    async def healthz() -> dict[str, object]:
        return {
            "status": "ok",
            "version": __version__,
            "redis": await ping_redis(),
        }

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "fleetkit_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_dev,
    )


if __name__ == "__main__":
    run()
