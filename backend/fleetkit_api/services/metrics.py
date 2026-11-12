from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models_ext import MetricSample


async def record_metric(
    db: AsyncSession,
    *,
    project_id: str,
    name: str,
    value: float,
    app_id: str | None = None,
    labels: dict[str, Any] | None = None,
) -> MetricSample:
    sample = MetricSample(
        project_id=project_id,
        app_id=app_id,
        name=name,
        value=value,
        labels=labels or {},
    )
    db.add(sample)
    await db.flush()
    return sample


async def query_metrics(
    db: AsyncSession,
    *,
    project_id: str,
    name: str,
    hours: int = 24,
) -> list[MetricSample]:
    since = datetime.now(UTC) - timedelta(hours=hours)
    result = await db.execute(
        select(MetricSample)
        .where(
            MetricSample.project_id == project_id,
            MetricSample.name == name,
            MetricSample.created_at >= since,
        )
        .order_by(MetricSample.created_at.asc())
        .limit(2000)
    )
    return list(result.scalars().all())


async def aggregate_avg(
    db: AsyncSession,
    *,
    project_id: str,
    name: str,
    hours: int = 24,
) -> float:
    since = datetime.now(UTC) - timedelta(hours=hours)
    value = await db.scalar(
        select(func.avg(MetricSample.value)).where(
            MetricSample.project_id == project_id,
            MetricSample.name == name,
            MetricSample.created_at >= since,
        )
    )
    return float(value or 0.0)


async def sum_metric(
    db: AsyncSession,
    *,
    project_id: str,
    name: str,
    hours: int = 24,
) -> float:
    since = datetime.now(UTC) - timedelta(hours=hours)
    value = await db.scalar(
        select(func.coalesce(func.sum(MetricSample.value), 0.0)).where(
            MetricSample.project_id == project_id,
            MetricSample.name == name,
            MetricSample.created_at >= since,
        )
    )
    return float(value or 0.0)


async def outcome_totals(
    db: AsyncSession, project_id: str, *, hours: int = 24
) -> dict[str, float]:
    names = ("jobs.succeeded", "jobs.failed", "jobs.retry")
    return {
        name: await sum_metric(db, project_id=project_id, name=name, hours=hours)
        for name in names
    }


async def snapshot_fleet_metrics(db: AsyncSession, project_id: str) -> dict[str, float]:
    from fleetkit_api.models import App, Job, JobStatus, Worker, WorkerStatus

    queued = await db.scalar(
        select(func.count())
        .select_from(Job)
        .join(App, App.id == Job.app_id)
        .where(App.project_id == project_id, Job.status == JobStatus.queued)
    )
    running = await db.scalar(
        select(func.count())
        .select_from(Job)
        .join(App, App.id == Job.app_id)
        .where(App.project_id == project_id, Job.status == JobStatus.running)
    )
    online = await db.scalar(
        select(func.count())
        .select_from(Worker)
        .join(App, App.id == Worker.app_id)
        .where(App.project_id == project_id, Worker.status == WorkerStatus.online)
    )
    values = {
        "jobs.queued": float(queued or 0),
        "jobs.running": float(running or 0),
        "workers.online": float(online or 0),
    }
    for name, value in values.items():
        await record_metric(db, project_id=project_id, name=name, value=value)
    return values
