from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Register extended tables for create_all
import fleetkit_api.models_ext as _models_ext  # noqa: F401
from fleetkit_api import __version__
from fleetkit_api.config import get_settings
from fleetkit_api.db import Base, SessionLocal, engine
from fleetkit_api.middleware import AgentRateLimitMiddleware, RequestIdMiddleware
from fleetkit_api.redis_client import ping_redis
from fleetkit_api.routers import (
    alerts,
    apps,
    auth,
    dlq,
    jobs,
    live,
    logs,
    metrics_router,
    ops,
    overview,
    projects,
    quotas,
    scenarios,
    schedules,
    secrets_router,
    templates,
    transfer,
    webhooks,
    workers,
)
from fleetkit_api.services.alerts import evaluate_all_alerts
from fleetkit_api.services.bootstrap import ensure_bootstrap_admin
from fleetkit_api.services.healthchecks import tick_health_checks
from fleetkit_api.services.retention import apply_all_retention
from fleetkit_api.services.schedules import tick_schedules
from fleetkit_api.services.workers import mark_stale_workers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("fleetkit.api")


async def _scheduler_loop(stop: asyncio.Event) -> None:
    ticks = 0
    while not stop.is_set():
        try:
            async with SessionLocal() as db:
                created = await tick_schedules(db)
                stale = await mark_stale_workers(db)
                health_ran = await tick_health_checks(db)
                ticks += 1
                fired = 0
                retained = 0
                if ticks % 4 == 0:
                    fired = await evaluate_all_alerts(db)
                if ticks % 40 == 0:
                    retained = await apply_all_retention(db)
                await db.commit()
                if created:
                    logger.info("Scheduler enqueued %s job(s)", created)
                if stale:
                    logger.info("Marked %s worker(s) offline after missed heartbeat", stale)
                if health_ran:
                    logger.info("Ran %s health check(s)", health_ran)
                if fired:
                    logger.info("Alert engine fired %s rule(s)", fired)
                if retained:
                    logger.info("Retention deleted %s row(s)", retained)
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
        description="Control plane for bots, workers, schedules, webhooks, alerts and secrets",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(AgentRateLimitMiddleware)
    for module in (
        auth,
        projects,
        apps,
        workers,
        jobs,
        schedules,
        webhooks,
        overview,
        alerts,
        secrets_router,
        logs,
        dlq,
        metrics_router,
        templates,
        ops,
        live,
        transfer,
        quotas,
        scenarios,
    ):
        app.include_router(module.router, prefix="/api/v1")

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
