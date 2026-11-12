from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Job, JobStatus, Worker, WorkerStatus
from fleetkit_api.services.cache import overview_cache
from fleetkit_api.services.events import emit_event


def _bust_overview() -> None:
    overview_cache.invalidate_prefix("overview")


async def enqueue_job(
    db: AsyncSession,
    *,
    app: App,
    name: str,
    payload: dict | None = None,
    queue: str = "default",
    max_attempts: int = 3,
    timeout_seconds: int = 300,
    scheduled_for: datetime | None = None,
    skip_payload_guard: bool = False,
) -> Job:
    if not skip_payload_guard:
        from fleetkit_api.security_suite.payload_guard import assert_payload_safe

        # Demo/fail jobs are allowed to carry attack strings for security drills.
        strict = not name.startswith(("demo.", "security.drill"))
        assert_payload_safe(payload, strict=strict)
    job = Job(
        app_id=app.id,
        name=name,
        queue=queue,
        payload=payload or {},
        max_attempts=max_attempts,
        timeout_seconds=timeout_seconds,
        scheduled_for=scheduled_for,
        status=JobStatus.queued,
    )
    db.add(job)
    await db.flush()
    await emit_event(
        db,
        project_id=app.project_id,
        app_id=app.id,
        job_id=job.id,
        kind="job.queued",
        message=f"Job {name} queued on {queue}",
        data={"queue": queue},
    )
    _bust_overview()
    return job


async def claim_next_job(
    db: AsyncSession,
    *,
    app: App,
    worker: Worker,
    queues: list[str] | None = None,
) -> Job | None:
    now = datetime.now(UTC)
    stmt = (
        select(Job)
        .where(
            Job.app_id == app.id,
            Job.status == JobStatus.queued,
            (Job.scheduled_for.is_(None)) | (Job.scheduled_for <= now),
        )
        .order_by(Job.created_at.asc())
        .limit(1)
    )
    # SKIP LOCKED is Postgres-only; SQLite smoke mode uses plain SELECT.
    settings_url = str(getattr(db.bind, "url", ""))
    if "sqlite" not in settings_url:
        stmt = stmt.with_for_update(skip_locked=True)
    if queues:
        stmt = stmt.where(Job.queue.in_(queues))

    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        return None

    job.status = JobStatus.running
    job.worker_id = worker.id
    job.attempt += 1
    job.started_at = now
    worker.status = WorkerStatus.online
    worker.last_heartbeat_at = now
    await emit_event(
        db,
        project_id=app.project_id,
        app_id=app.id,
        job_id=job.id,
        kind="job.started",
        message=f"Worker {worker.name} claimed job {job.name}",
        data={"worker_id": worker.id, "attempt": job.attempt},
    )
    await db.flush()
    _bust_overview()
    return job


async def claim_jobs_batch(
    db: AsyncSession,
    *,
    app: App,
    worker: Worker,
    queues: list[str] | None = None,
    limit: int = 5,
) -> list[Job]:
    """Claim up to `limit` queued jobs in one round-trip (fewer heartbeats under load)."""
    limit = max(1, min(limit, 25))
    claimed: list[Job] = []
    for _ in range(limit):
        job = await claim_next_job(db, app=app, worker=worker, queues=queues)
        if job is None:
            break
        claimed.append(job)
    return claimed


async def cancel_job(db: AsyncSession, job: Job) -> Job:
    if job.status not in (JobStatus.queued, JobStatus.running):
        return job
    job.status = JobStatus.cancelled
    job.finished_at = datetime.now(UTC)
    job.worker_id = None
    app = await db.get(App, job.app_id)
    if app:
        await emit_event(
            db,
            project_id=app.project_id,
            app_id=app.id,
            job_id=job.id,
            kind="job.cancelled",
            message=f"Job {job.name} cancelled",
            level="warning",
        )
    await db.flush()
    _bust_overview()
    return job


async def cancel_jobs_bulk(db: AsyncSession, jobs: list[Job]) -> list[Job]:
    out: list[Job] = []
    for job in jobs:
        out.append(await cancel_job(db, job))
    return out


async def complete_job(db: AsyncSession, job: Job, result: dict) -> Job:
    job.status = JobStatus.succeeded
    job.result = result
    job.error = None
    job.finished_at = datetime.now(UTC)
    app = await db.get(App, job.app_id)
    if app:
        await emit_event(
            db,
            project_id=app.project_id,
            app_id=app.id,
            job_id=job.id,
            kind="job.succeeded",
            message=f"Job {job.name} succeeded",
        )
    await db.flush()
    _bust_overview()
    return job


async def fail_job(db: AsyncSession, job: Job, error: str, *, retry: bool = True) -> Job:
    from fleetkit_api.services.backoff import next_retry_at
    from fleetkit_api.services.dlq import push_dead_letter
    from fleetkit_api.services.live import live_hub

    app = await db.get(App, job.app_id)
    if retry and job.attempt < job.max_attempts:
        job.status = JobStatus.queued
        job.worker_id = None
        job.started_at = None
        job.error = error
        job.scheduled_for = next_retry_at(job.attempt)
        kind = "job.retry"
        message = f"Job {job.name} failed, re-queued ({job.attempt}/{job.max_attempts})"
    else:
        job.status = JobStatus.failed
        job.error = error
        job.finished_at = datetime.now(UTC)
        kind = "job.failed"
        message = f"Job {job.name} failed: {error[:200]}"
        if app:
            await push_dead_letter(db, job=job, error=error)

    if app:
        await emit_event(
            db,
            project_id=app.project_id,
            app_id=app.id,
            job_id=job.id,
            level="error" if job.status == JobStatus.failed else "warning",
            kind=kind,
            message=message,
            data={"error": error},
        )
        await live_hub.publish(
            app.project_id,
            kind,
            {"job_id": job.id, "name": job.name, "status": job.status.value},
        )
    await db.flush()
    _bust_overview()
    return job
