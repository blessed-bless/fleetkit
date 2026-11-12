from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_by_api_key, get_project_for_user
from fleetkit_api.models import App, Job, Project, Worker
from fleetkit_api.schemas import JobCompleteIn, JobCreate, JobFailIn, JobOut
from fleetkit_api.services.jobs import claim_next_job, complete_job, enqueue_job, fail_job

router = APIRouter(tags=["jobs"])


async def _app_in_project(db: AsyncSession, project: Project, app_id: str) -> App:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    return app


@router.get("/projects/{project_id}/jobs", response_model=list[JobOut])
async def list_jobs(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    app_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Job]:
    stmt = (
        select(Job)
        .join(App, App.id == Job.app_id)
        .where(App.project_id == project.id)
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    if app_id:
        stmt = stmt.where(Job.app_id == app_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/projects/{project_id}/apps/{app_id}/jobs", response_model=JobOut, status_code=201)
async def create_job(
    app_id: str,
    body: JobCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    app = await _app_in_project(db, project, app_id)
    job = await enqueue_job(
        db,
        app=app,
        name=body.name,
        payload=body.payload,
        queue=body.queue,
        max_attempts=body.max_attempts,
        timeout_seconds=body.timeout_seconds,
        scheduled_for=body.scheduled_for,
    )
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/agent/apps/{app_id}/jobs", response_model=JobOut, status_code=201)
async def agent_enqueue(
    app_id: str,
    body: JobCreate,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> Job:
    app = await _app_in_project(db, project, app_id)
    job = await enqueue_job(
        db,
        app=app,
        name=body.name,
        payload=body.payload,
        queue=body.queue,
        max_attempts=body.max_attempts,
        timeout_seconds=body.timeout_seconds,
        scheduled_for=body.scheduled_for,
    )
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/agent/workers/{worker_id}/claim", response_model=JobOut | None)
async def agent_claim(
    worker_id: str,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
    queue: list[str] | None = Query(default=None),
) -> Job | None:
    worker = await db.get(Worker, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker не найден")
    app = await db.get(App, worker.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Worker не найден")
    job = await claim_next_job(db, app=app, worker=worker, queues=queue)
    await db.commit()
    if job:
        await db.refresh(job)
    return job


@router.post("/agent/jobs/{job_id}/complete", response_model=JobOut)
async def agent_complete(
    job_id: str,
    body: JobCompleteIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job не найден")
    app = await db.get(App, job.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Job не найден")
    await complete_job(db, job, body.result)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/agent/jobs/{job_id}/fail", response_model=JobOut)
async def agent_fail(
    job_id: str,
    body: JobFailIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job не найден")
    app = await db.get(App, job.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Job не найден")
    await fail_job(db, job, body.error, retry=body.retry)
    await db.commit()
    await db.refresh(job)
    return job
