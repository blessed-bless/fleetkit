from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Job, JobStatus, Worker
from fleetkit_api.models_ext import SecretRecord


@dataclass
class ProjectQuota:
    max_apps: int = 100
    max_workers_per_app: int = 50
    max_queued_jobs: int = 5000
    max_secrets: int = 200


DEFAULT_QUOTA = ProjectQuota()


async def count_apps(db: AsyncSession, project_id: str) -> int:
    return int(
        await db.scalar(select(func.count()).select_from(App).where(App.project_id == project_id))
        or 0
    )


async def count_queued(db: AsyncSession, project_id: str) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(Job)
            .join(App, App.id == Job.app_id)
            .where(App.project_id == project_id, Job.status == JobStatus.queued)
        )
        or 0
    )


async def count_secrets(db: AsyncSession, project_id: str) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(SecretRecord)
            .where(SecretRecord.project_id == project_id)
        )
        or 0
    )


async def count_workers_for_app(db: AsyncSession, app_id: str) -> int:
    return int(
        await db.scalar(select(func.count()).select_from(Worker).where(Worker.app_id == app_id))
        or 0
    )


async def assert_can_create_app(db: AsyncSession, project_id: str, quota: ProjectQuota = DEFAULT_QUOTA) -> None:
    if await count_apps(db, project_id) >= quota.max_apps:
        raise ValueError(f"app quota exceeded ({quota.max_apps})")


async def assert_can_enqueue(db: AsyncSession, project_id: str, quota: ProjectQuota = DEFAULT_QUOTA) -> None:
    if await count_queued(db, project_id) >= quota.max_queued_jobs:
        raise ValueError(f"queued jobs quota exceeded ({quota.max_queued_jobs})")


async def assert_can_add_secret(db: AsyncSession, project_id: str, quota: ProjectQuota = DEFAULT_QUOTA) -> None:
    if await count_secrets(db, project_id) >= quota.max_secrets:
        raise ValueError(f"secrets quota exceeded ({quota.max_secrets})")


async def quota_snapshot(db: AsyncSession, project_id: str, quota: ProjectQuota = DEFAULT_QUOTA) -> dict:
    return {
        "apps": {"used": await count_apps(db, project_id), "max": quota.max_apps},
        "queued_jobs": {"used": await count_queued(db, project_id), "max": quota.max_queued_jobs},
        "secrets": {"used": await count_secrets(db, project_id), "max": quota.max_secrets},
        "workers_per_app_max": quota.max_workers_per_app,
    }
