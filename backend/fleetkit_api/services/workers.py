from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.config import get_settings
from fleetkit_api.models import Worker, WorkerStatus


async def mark_stale_workers(db: AsyncSession) -> int:
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.worker_stale_seconds)
    result = await db.execute(
        update(Worker)
        .where(
            Worker.status == WorkerStatus.online,
            Worker.last_heartbeat_at.is_not(None),
            Worker.last_heartbeat_at < cutoff,
        )
        .values(status=WorkerStatus.offline)
        .returning(Worker.id)
    )
    ids = result.scalars().all()
    return len(ids)


async def list_online(db: AsyncSession, *, app_id: str | None = None) -> list[Worker]:
    stmt = select(Worker).where(Worker.status == WorkerStatus.online)
    if app_id:
        stmt = stmt.where(Worker.app_id == app_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
