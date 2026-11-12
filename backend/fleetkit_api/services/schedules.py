from __future__ import annotations

from datetime import UTC, datetime

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Schedule
from fleetkit_api.services.jobs import enqueue_job


def compute_next_run(cron: str, *, base: datetime | None = None) -> datetime:
    base = base or datetime.now(UTC)
    # croniter expects naive or aware consistently; keep UTC aware
    itr = croniter(cron, base)
    nxt = itr.get_next(datetime)
    if nxt.tzinfo is None:
        nxt = nxt.replace(tzinfo=UTC)
    return nxt


async def tick_schedules(db: AsyncSession) -> int:
    now = datetime.now(UTC)
    result = await db.execute(select(Schedule).where(Schedule.is_enabled.is_(True)))
    schedules = result.scalars().all()
    created = 0
    for schedule in schedules:
        if schedule.next_run_at is None:
            schedule.next_run_at = compute_next_run(schedule.cron, base=now)
            continue
        if schedule.next_run_at > now:
            continue
        app = await db.get(App, schedule.app_id)
        if app is None or not app.is_enabled:
            schedule.next_run_at = compute_next_run(schedule.cron, base=now)
            continue
        await enqueue_job(
            db,
            app=app,
            name=f"schedule:{schedule.name}",
            payload={**schedule.payload, "_schedule_id": schedule.id},
            queue="scheduled",
        )
        schedule.last_run_at = now
        schedule.next_run_at = compute_next_run(schedule.cron, base=now)
        created += 1
    await db.flush()
    return created
