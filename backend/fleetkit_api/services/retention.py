from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import Event, Job, JobStatus
from fleetkit_api.models_ext import DeadLetter, JobLogChunk, MetricSample, RetentionPolicy

logger = logging.getLogger("fleetkit.retention")

DEFAULTS = {
    "events": 30,
    "job_logs": 14,
    "metrics": 30,
    "dead_letters": 60,
    "jobs": 45,
}


async def ensure_default_policies(db: AsyncSession, project_id: str) -> None:
    existing = (
        await db.execute(select(RetentionPolicy).where(RetentionPolicy.project_id == project_id))
    ).scalars().all()
    have = {p.kind for p in existing}
    for kind, days in DEFAULTS.items():
        if kind in have:
            continue
        db.add(
            RetentionPolicy(project_id=project_id, kind=kind, keep_days=days, is_enabled=True)
        )
    await db.flush()


async def apply_retention(db: AsyncSession, project_id: str) -> dict[str, int]:
    await ensure_default_policies(db, project_id)
    policies = (
        await db.execute(
            select(RetentionPolicy).where(
                RetentionPolicy.project_id == project_id,
                RetentionPolicy.is_enabled.is_(True),
            )
        )
    ).scalars().all()
    deleted: dict[str, int] = {}
    now = datetime.now(UTC)
    for policy in policies:
        cutoff = now - timedelta(days=policy.keep_days)
        if policy.kind == "events":
            result = await db.execute(
                delete(Event).where(Event.project_id == project_id, Event.created_at < cutoff)
            )
            deleted["events"] = result.rowcount or 0
        elif policy.kind == "job_logs":
            result = await db.execute(
                delete(JobLogChunk).where(
                    JobLogChunk.project_id == project_id, JobLogChunk.created_at < cutoff
                )
            )
            deleted["job_logs"] = result.rowcount or 0
        elif policy.kind == "metrics":
            result = await db.execute(
                delete(MetricSample).where(
                    MetricSample.project_id == project_id, MetricSample.created_at < cutoff
                )
            )
            deleted["metrics"] = result.rowcount or 0
        elif policy.kind == "dead_letters":
            result = await db.execute(
                delete(DeadLetter).where(
                    DeadLetter.project_id == project_id,
                    DeadLetter.created_at < cutoff,
                    DeadLetter.requeued.is_(True),
                )
            )
            deleted["dead_letters"] = result.rowcount or 0
        elif policy.kind == "jobs":
            result = await db.execute(
                delete(Job).where(
                    Job.created_at < cutoff,
                    Job.status.in_(
                        [JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled, JobStatus.timed_out]
                    ),
                )
            )
            deleted["jobs"] = result.rowcount or 0
    await db.flush()
    if any(deleted.values()):
        logger.info("retention project=%s deleted=%s", project_id, deleted)
    return deleted


async def apply_all_retention(db: AsyncSession) -> int:
    from fleetkit_api.models import Project

    ids = (await db.execute(select(Project.id))).scalars().all()
    total = 0
    for project_id in ids:
        deleted = await apply_retention(db, project_id)
        total += sum(deleted.values())
    return total
