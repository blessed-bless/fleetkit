from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import App, Project
from fleetkit_api.models_ext import JobPriorityOverride, JobTemplate
from fleetkit_api.schemas_ext import BatchJobCreate, TemplateCreate, TemplateOut
from fleetkit_api.services.jobs import enqueue_job

router = APIRouter(tags=["templates"])


@router.get("/projects/{project_id}/templates", response_model=list[TemplateOut])
async def list_templates(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobTemplate]:
    result = await db.execute(
        select(JobTemplate)
        .where(JobTemplate.project_id == project.id)
        .order_by(JobTemplate.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/projects/{project_id}/templates", response_model=TemplateOut, status_code=201)
async def create_template(
    body: TemplateCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> JobTemplate:
    app = await db.get(App, body.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    existing = await db.execute(
        select(JobTemplate).where(
            JobTemplate.project_id == project.id, JobTemplate.slug == body.slug
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug шаблона занят")
    row = JobTemplate(
        project_id=project.id,
        app_id=body.app_id,
        slug=body.slug,
        name=body.name,
        job_name=body.job_name,
        queue=body.queue,
        priority=body.priority,
        payload=body.payload,
        max_attempts=body.max_attempts,
        timeout_seconds=body.timeout_seconds,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/projects/{project_id}/templates/{template_id}/run")
async def run_template(
    template_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = await db.get(JobTemplate, template_id)
    if row is None or row.project_id != project.id:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    app = await db.get(App, row.app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App не найдено")
    job = await enqueue_job(
        db,
        app=app,
        name=row.job_name,
        payload={**row.payload, "_template": row.slug},
        queue=row.queue,
        max_attempts=row.max_attempts,
        timeout_seconds=row.timeout_seconds,
    )
    db.add(JobPriorityOverride(job_id=job.id, priority=row.priority))
    await db.commit()
    return {"job_id": job.id}


@router.post("/projects/{project_id}/jobs/batch")
async def batch_enqueue(
    body: BatchJobCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if len(body.payloads) > 500:
        raise HTTPException(status_code=400, detail="Максимум 500 payload за раз")
    app = await db.get(App, body.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    ids: list[str] = []
    for payload in body.payloads:
        job = await enqueue_job(
            db,
            app=app,
            name=body.name,
            payload=payload,
            queue=body.queue,
        )
        db.add(JobPriorityOverride(job_id=job.id, priority=body.priority))
        ids.append(job.id)
    await db.commit()
    return {"count": len(ids), "job_ids": ids}
