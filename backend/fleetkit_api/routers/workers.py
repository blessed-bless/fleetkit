from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_by_api_key, get_project_for_user
from fleetkit_api.models import App, Project, Worker, WorkerStatus
from fleetkit_api.schemas import WorkerDrainIn, WorkerHeartbeatIn, WorkerOut, WorkerRegisterIn
from fleetkit_api.services.events import emit_event

router = APIRouter(tags=["workers"])


async def _get_app_in_project(db: AsyncSession, project: Project, app_id: str) -> App:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    return app


@router.get("/projects/{project_id}/workers", response_model=list[WorkerOut])
async def list_workers(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    app_id: str | None = Query(default=None),
) -> list[Worker]:
    stmt = (
        select(Worker)
        .join(App, App.id == Worker.app_id)
        .where(App.project_id == project.id)
        .order_by(Worker.created_at.desc())
    )
    if app_id:
        stmt = stmt.where(Worker.app_id == app_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/agent/apps/{app_id}/workers/register", response_model=WorkerOut, status_code=201)
async def register_worker(
    app_id: str,
    body: WorkerRegisterIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> Worker:
    app = await _get_app_in_project(db, project, app_id)
    worker = Worker(
        app_id=app.id,
        name=body.name,
        hostname=body.hostname,
        labels=body.labels,
        meta=body.meta,
        status=WorkerStatus.online,
        last_heartbeat_at=datetime.now(UTC),
    )
    db.add(worker)
    await db.flush()
    await emit_event(
        db,
        project_id=project.id,
        app_id=app.id,
        kind="worker.registered",
        message=f"Worker {worker.name} registered",
        data={"hostname": worker.hostname},
    )
    await db.commit()
    await db.refresh(worker)
    return worker


@router.post("/agent/workers/{worker_id}/heartbeat", response_model=WorkerOut)
async def heartbeat(
    worker_id: str,
    body: WorkerHeartbeatIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> Worker:
    worker = await db.get(Worker, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker не найден")
    app = await db.get(App, worker.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Worker не найден")
    worker.status = body.status
    worker.meta = {**worker.meta, **body.meta}
    worker.last_heartbeat_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(worker)
    return worker


@router.post("/projects/{project_id}/workers/{worker_id}/drain", response_model=WorkerOut)
async def drain_worker(
    worker_id: str,
    body: WorkerDrainIn,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> Worker:
    """Mark worker draining (no new claims) or bring it back online."""
    worker = await db.get(Worker, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker не найден")
    app = await db.get(App, worker.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Worker не найден")
    worker.status = WorkerStatus.draining if body.draining else WorkerStatus.online
    worker.last_heartbeat_at = datetime.now(UTC)
    await emit_event(
        db,
        project_id=project.id,
        app_id=app.id,
        kind="worker.drain" if body.draining else "worker.online",
        message=f"Worker {worker.name} {'draining' if body.draining else 'online'}",
        data={"worker_id": worker.id},
    )
    await db.commit()
    await db.refresh(worker)
    return worker
