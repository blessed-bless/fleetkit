from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_by_api_key, get_project_for_user
from fleetkit_api.models import App, Job, JobStatus, Project, Worker
from fleetkit_api.schemas import JobCompleteIn, JobCreate, JobFailIn, JobOut
from fleetkit_api.services.jobs import (
    PolicyDenied,
    cancel_job,
    cancel_jobs_bulk,
    claim_jobs_batch,
    claim_next_job,
    complete_job,
    enqueue_job,
    fail_job,
    retry_job,
)

router = APIRouter(tags=["jobs"])


class JobBulkCancelIn(BaseModel):
    job_ids: list[str] = Field(min_length=1, max_length=100)


async def _app_in_project(db: AsyncSession, project: Project, app_id: str) -> App:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    return app


async def _job_in_project(db: AsyncSession, project: Project, job_id: str) -> Job:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job не найден")
    app = await db.get(App, job.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Job не найден")
    return job


@router.get("/projects/{project_id}/jobs", response_model=list[JobOut])
async def list_jobs(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    app_id: str | None = Query(default=None),
    status: JobStatus | None = Query(default=None),
    queue: str | None = Query(default=None),
    tag: str | None = Query(default=None, max_length=64),
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Job]:
    fetch_limit = min(limit * 4, 400) if tag else limit
    stmt = (
        select(Job)
        .join(App, App.id == Job.app_id)
        .where(App.project_id == project.id)
        .order_by(Job.created_at.desc())
        .limit(fetch_limit)
    )
    if app_id:
        stmt = stmt.where(Job.app_id == app_id)
    if status:
        stmt = stmt.where(Job.status == status)
    if queue:
        stmt = stmt.where(Job.queue == queue)
    if q:
        stmt = stmt.where(Job.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    if tag:
        rows = [j for j in rows if tag in (j.tags or [])][:limit]
    return rows


@router.get("/projects/{project_id}/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    return await _job_in_project(db, project, job_id)


@router.post("/projects/{project_id}/jobs/{job_id}/cancel", response_model=JobOut)
async def cancel_one(
    job_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = await _job_in_project(db, project, job_id)
    await cancel_job(db, job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/projects/{project_id}/jobs/{job_id}/retry", response_model=JobOut)
async def retry_one(
    job_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = await _job_in_project(db, project, job_id)
    try:
        await retry_job(db, job)
    except PolicyDenied as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/projects/{project_id}/jobs/cancel-bulk", response_model=list[JobOut])
async def cancel_bulk(
    body: JobBulkCancelIn,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[Job]:
    jobs: list[Job] = []
    for job_id in body.job_ids:
        try:
            jobs.append(await _job_in_project(db, project, job_id))
        except HTTPException:
            continue
    updated = await cancel_jobs_bulk(db, jobs)
    await db.commit()
    for job in updated:
        await db.refresh(job)
    return updated


@router.post("/projects/{project_id}/apps/{app_id}/jobs", response_model=JobOut, status_code=201)
async def create_job(
    app_id: str,
    body: JobCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> Job:
    app = await _app_in_project(db, project, app_id)
    try:
        job = await enqueue_job(
            db,
            app=app,
            name=body.name,
            payload=body.payload,
            queue=body.queue,
            tags=body.tags,
            max_attempts=body.max_attempts,
            timeout_seconds=body.timeout_seconds,
            scheduled_for=body.scheduled_for,
        )
    except PolicyDenied as exc:
        raise HTTPException(status_code=409, detail=f"policy denied: {exc.reason}") from exc
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
    try:
        job = await enqueue_job(
            db,
            app=app,
            name=body.name,
            payload=body.payload,
            queue=body.queue,
            tags=body.tags,
            max_attempts=body.max_attempts,
            timeout_seconds=body.timeout_seconds,
            scheduled_for=body.scheduled_for,
        )
    except PolicyDenied as exc:
        raise HTTPException(status_code=409, detail=f"policy denied: {exc.reason}") from exc
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


@router.post("/agent/workers/{worker_id}/claim-batch", response_model=list[JobOut])
async def agent_claim_batch(
    worker_id: str,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
    queue: list[str] | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=25),
) -> list[Job]:
    worker = await db.get(Worker, worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker не найден")
    app = await db.get(App, worker.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Worker не найден")
    jobs = await claim_jobs_batch(db, app=app, worker=worker, queues=queue, limit=limit)
    await db.commit()
    for job in jobs:
        await db.refresh(job)
    return jobs


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
