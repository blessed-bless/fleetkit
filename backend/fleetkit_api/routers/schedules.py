from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user, require_permission
from fleetkit_api.models import App, Project, Schedule
from fleetkit_api.schemas import ScheduleCreate, ScheduleOut
from fleetkit_api.security_suite.rbac import Permission
from fleetkit_api.services.schedules import compute_next_run

router = APIRouter(tags=["schedules"])


class SchedulePatch(BaseModel):
    is_enabled: bool | None = None
    cron: str | None = None
    name: str | None = None


@router.get("/projects/{project_id}/schedules", response_model=list[ScheduleOut])
async def list_schedules(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[Schedule]:
    result = await db.execute(
        select(Schedule)
        .join(App, App.id == Schedule.app_id)
        .where(App.project_id == project.id)
        .order_by(Schedule.created_at.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/apps/{app_id}/schedules",
    response_model=ScheduleOut,
    status_code=201,
)
async def create_schedule(
    app_id: str,
    body: ScheduleCreate,
    project: Project = Depends(require_permission(Permission.app_write)),
    db: AsyncSession = Depends(get_db),
) -> Schedule:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    try:
        next_run = compute_next_run(body.cron)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"Неверный cron: {exc}") from exc
    schedule = Schedule(
        app_id=app.id,
        name=body.name,
        cron=body.cron,
        timezone=body.timezone,
        payload=body.payload,
        is_enabled=body.is_enabled,
        next_run_at=next_run,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.patch("/projects/{project_id}/schedules/{schedule_id}", response_model=ScheduleOut)
async def patch_schedule(
    schedule_id: str,
    body: SchedulePatch,
    project: Project = Depends(require_permission(Permission.app_write)),
    db: AsyncSession = Depends(get_db),
) -> Schedule:
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule не найден")
    app = await db.get(App, schedule.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Schedule не найден")
    if body.name is not None:
        schedule.name = body.name
    if body.is_enabled is not None:
        schedule.is_enabled = body.is_enabled
    if body.cron is not None:
        try:
            schedule.cron = body.cron
            schedule.next_run_at = compute_next_run(body.cron)
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=f"Неверный cron: {exc}") from exc
    await db.commit()
    await db.refresh(schedule)
    return schedule
