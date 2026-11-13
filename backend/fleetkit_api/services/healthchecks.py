from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import Worker, WorkerStatus
from fleetkit_api.models_ext import HealthCheck

logger = logging.getLogger("fleetkit.health")


async def run_health_check(db: AsyncSession, check: HealthCheck) -> HealthCheck:
    from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url

    now = datetime.now(UTC)
    check.last_checked_at = now
    try:
        if check.kind == "http":
            try:
                target = assert_safe_url(str(check.target))
            except SSRFBlocked as exc:
                check.last_status = "down"
                check.last_error = f"ssrf blocked: {exc}"
                await db.flush()
                return check
            async with httpx.AsyncClient(
                timeout=check.timeout_seconds, follow_redirects=False
            ) as client:
                resp = await client.get(target)
                if resp.status_code >= 400:
                    check.last_status = "down"
                    check.last_error = f"HTTP {resp.status_code}"
                else:
                    check.last_status = "up"
                    check.last_error = ""
        elif check.kind == "worker_heartbeat":
            worker = await db.scalar(
                select(Worker)
                .where(Worker.app_id == check.app_id, Worker.status == WorkerStatus.online)
                .limit(1)
            )
            if worker is None:
                check.last_status = "down"
                check.last_error = "no online workers"
            else:
                check.last_status = "up"
                check.last_error = ""
        else:
            check.last_status = "unknown"
            check.last_error = f"unsupported kind {check.kind}"
    except Exception as exc:
        check.last_status = "down"
        check.last_error = str(exc)[:500]
        logger.warning("health check %s failed: %s", check.id, exc)
    await db.flush()
    return check


async def tick_health_checks(db: AsyncSession) -> int:
    checks = (
        await db.execute(select(HealthCheck).where(HealthCheck.is_enabled.is_(True)))
    ).scalars().all()
    now = datetime.now(UTC)
    ran = 0
    for check in checks:
        due = True
        if check.last_checked_at is not None:
            elapsed = (now - check.last_checked_at).total_seconds()
            due = elapsed >= check.interval_seconds
        if not due:
            continue
        await run_health_check(db, check)
        ran += 1
    return ran
