from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user, require_permission
from fleetkit_api.models import App, Project
from fleetkit_api.schemas import AppCreate, AppOut, AppUpdate
from fleetkit_api.security_suite.rbac import Permission
from fleetkit_api.services.events import emit_event

router = APIRouter(tags=["apps"])


@router.get("/projects/{project_id}/apps", response_model=list[AppOut])
async def list_apps(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[App]:
    result = await db.execute(
        select(App).where(App.project_id == project.id).order_by(App.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/projects/{project_id}/apps", response_model=AppOut, status_code=201)
async def create_app(
    body: AppCreate,
    project: Project = Depends(require_permission(Permission.app_write)),
    db: AsyncSession = Depends(get_db),
) -> App:
    existing = await db.execute(
        select(App).where(App.project_id == project.id, App.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="App slug уже есть в проекте")
    app = App(
        project_id=project.id,
        slug=body.slug,
        name=body.name,
        kind=body.kind,
        config=body.config,
    )
    db.add(app)
    await db.flush()
    await emit_event(
        db,
        project_id=project.id,
        app_id=app.id,
        kind="app.created",
        message=f"App {app.slug} created",
    )
    await db.commit()
    await db.refresh(app)
    return app


@router.patch("/projects/{project_id}/apps/{app_id}", response_model=AppOut)
async def update_app(
    app_id: str,
    body: AppUpdate,
    project: Project = Depends(require_permission(Permission.app_write)),
    db: AsyncSession = Depends(get_db),
) -> App:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    if body.name is not None:
        app.name = body.name
    if body.is_enabled is not None:
        app.is_enabled = body.is_enabled
    if body.config is not None:
        app.config = body.config
    await db.commit()
    await db.refresh(app)
    return app


@router.get("/projects/{project_id}/apps/{app_id}", response_model=AppOut)
async def get_app(
    app_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> App:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    return app
