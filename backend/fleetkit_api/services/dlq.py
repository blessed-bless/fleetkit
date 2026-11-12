from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Job
from fleetkit_api.models_ext import DeadLetter
from fleetkit_api.services.events import emit_event
from fleetkit_api.services.jobs import enqueue_job


async def push_dead_letter(
    db: AsyncSession,
    *,
    job: Job,
    error: str,
) -> DeadLetter:
    app = await db.get(App, job.app_id)
    if app is None:
        raise ValueError("job app missing")
    item = DeadLetter(
        project_id=app.project_id,
        app_id=app.id,
        job_id=job.id,
        job_name=job.name,
        payload=job.payload or {},
        error=error,
        attempts=job.attempt,
    )
    db.add(item)
    await db.flush()
    await emit_event(
        db,
        project_id=app.project_id,
        app_id=app.id,
        job_id=job.id,
        level="error",
        kind="dlq.pushed",
        message=f"Job {job.name} moved to dead letter",
        data={"dlq_id": item.id},
    )
    return item


async def requeue_dead_letter(db: AsyncSession, item: DeadLetter) -> Job:
    if item.requeued:
        raise ValueError("already requeued")
    app = await db.get(App, item.app_id)
    if app is None:
        raise ValueError("app missing")
    job = await enqueue_job(
        db,
        app=app,
        name=item.job_name,
        payload={**item.payload, "_requeued_from_dlq": item.id},
        queue="default",
    )
    item.requeued = True
    await emit_event(
        db,
        project_id=item.project_id,
        app_id=item.app_id,
        job_id=job.id,
        kind="dlq.requeued",
        message=f"Dead letter {item.id} requeued as {job.id}",
    )
    await db.flush()
    return job


async def list_dead_letters(
    db: AsyncSession, *, project_id: str, include_requeued: bool = False
) -> list[DeadLetter]:
    stmt = (
        select(DeadLetter)
        .where(DeadLetter.project_id == project_id)
        .order_by(DeadLetter.created_at.desc())
        .limit(200)
    )
    if not include_requeued:
        stmt = stmt.where(DeadLetter.requeued.is_(False))
    result = await db.execute(stmt)
    return list(result.scalars().all())
