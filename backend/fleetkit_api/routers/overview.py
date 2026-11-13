from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user
from fleetkit_api.models import App, Event, Job, JobStatus, User, Worker, WorkerStatus
from fleetkit_api.schemas import EventOut, OverviewOut
from fleetkit_api.services.cache import overview_cache
from fleetkit_api.services.membership import accessible_project_ids

router = APIRouter(tags=["overview"])


@router.get("/overview", response_model=OverviewOut)
async def overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OverviewOut:
    cache_key = ("overview", user.id)
    cached = overview_cache.get(cache_key)
    if cached is not None:
        return cached

    project_ids = await accessible_project_ids(db, user)
    projects_count = len(project_ids)

    if not project_ids:
        empty = OverviewOut(
            projects=0,
            apps=0,
            workers_online=0,
            jobs_queued=0,
            jobs_running=0,
            jobs_failed_24h=0,
            recent_events=[],
        )
        overview_cache.set(cache_key, empty, ttl_seconds=2.0)
        return empty

    apps_count = await db.scalar(
        select(func.count()).select_from(App).where(App.project_id.in_(project_ids))
    )
    workers_online = await db.scalar(
        select(func.count())
        .select_from(Worker)
        .join(App, App.id == Worker.app_id)
        .where(App.project_id.in_(project_ids), Worker.status == WorkerStatus.online)
    )
    jobs_queued = await db.scalar(
        select(func.count())
        .select_from(Job)
        .join(App, App.id == Job.app_id)
        .where(App.project_id.in_(project_ids), Job.status == JobStatus.queued)
    )
    jobs_running = await db.scalar(
        select(func.count())
        .select_from(Job)
        .join(App, App.id == Job.app_id)
        .where(App.project_id.in_(project_ids), Job.status == JobStatus.running)
    )
    since = datetime.now(UTC) - timedelta(hours=24)
    jobs_failed_24h = await db.scalar(
        select(func.count())
        .select_from(Job)
        .join(App, App.id == Job.app_id)
        .where(
            App.project_id.in_(project_ids),
            Job.status == JobStatus.failed,
            Job.finished_at >= since,
        )
    )
    events = (
        await db.execute(
            select(Event)
            .where(Event.project_id.in_(project_ids))
            .order_by(Event.created_at.desc())
            .limit(20)
        )
    ).scalars().all()

    result = OverviewOut(
        projects=projects_count or 0,
        apps=apps_count or 0,
        workers_online=workers_online or 0,
        jobs_queued=jobs_queued or 0,
        jobs_running=jobs_running or 0,
        jobs_failed_24h=jobs_failed_24h or 0,
        recent_events=[EventOut.model_validate(e) for e in events],
    )
    overview_cache.set(cache_key, result, ttl_seconds=2.0)
    return result
