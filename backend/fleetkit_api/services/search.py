from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Event, Job, Worker
from fleetkit_api.models_ext import DeadLetter


async def search_project(db: AsyncSession, *, project_id: str, q: str, limit: int = 40) -> dict:
    needle = f"%{q.strip()}%"
    if len(q.strip()) < 2:
        return {"apps": [], "jobs": [], "workers": [], "events": [], "dead_letters": []}

    apps = (
        await db.execute(
            select(App)
            .where(App.project_id == project_id, or_(App.name.ilike(needle), App.slug.ilike(needle)))
            .limit(limit)
        )
    ).scalars().all()

    jobs = (
        await db.execute(
            select(Job)
            .join(App, App.id == Job.app_id)
            .where(
                App.project_id == project_id,
                or_(Job.name.ilike(needle), Job.id.ilike(needle), Job.error.ilike(needle)),
            )
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    workers = (
        await db.execute(
            select(Worker)
            .join(App, App.id == Worker.app_id)
            .where(
                App.project_id == project_id,
                or_(Worker.name.ilike(needle), Worker.hostname.ilike(needle)),
            )
            .limit(limit)
        )
    ).scalars().all()

    events = (
        await db.execute(
            select(Event)
            .where(
                Event.project_id == project_id,
                or_(Event.message.ilike(needle), Event.kind.ilike(needle)),
            )
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    dead = (
        await db.execute(
            select(DeadLetter)
            .where(
                DeadLetter.project_id == project_id,
                or_(DeadLetter.job_name.ilike(needle), DeadLetter.error.ilike(needle)),
            )
            .limit(limit)
        )
    ).scalars().all()

    return {
        "apps": [{"id": a.id, "name": a.name, "slug": a.slug} for a in apps],
        "jobs": [{"id": j.id, "name": j.name, "status": j.status.value} for j in jobs],
        "workers": [{"id": w.id, "name": w.name, "status": w.status.value} for w in workers],
        "events": [{"id": e.id, "kind": e.kind, "message": e.message} for e in events],
        "dead_letters": [{"id": d.id, "job_name": d.job_name, "error": d.error[:200]} for d in dead],
    }
