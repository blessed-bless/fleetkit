from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_by_api_key, get_project_for_user
from fleetkit_api.models import App, Job, Project
from fleetkit_api.schemas_ext import LogBatchIn, LogChunkOut, LogLineIn
from fleetkit_api.services.logs import append_lines, append_log, read_logs

router = APIRouter(tags=["logs"])


async def _job_in_project(db: AsyncSession, project: Project, job_id: str) -> Job:
    job = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job не найден")
    app = await db.get(App, job.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="Job не найден")
    return job


@router.get("/projects/{project_id}/jobs/{job_id}/logs", response_model=list[LogChunkOut])
async def get_logs(
    job_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    after_seq: int = Query(default=0, ge=0),
) -> list:
    await _job_in_project(db, project, job_id)
    return await read_logs(db, job_id=job_id, after_seq=after_seq)


@router.post("/agent/jobs/{job_id}/logs", response_model=LogChunkOut, status_code=201)
async def agent_log_line(
    job_id: str,
    body: LogLineIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    await _job_in_project(db, project, job_id)
    chunk = await append_log(
        db,
        project_id=project.id,
        job_id=job_id,
        line=body.line,
        stream=body.stream,
        seq=body.seq,
    )
    await db.commit()
    await db.refresh(chunk)
    return chunk


@router.post("/agent/jobs/{job_id}/logs/batch")
async def agent_log_batch(
    job_id: str,
    body: LogBatchIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    await _job_in_project(db, project, job_id)
    count = await append_lines(
        db,
        project_id=project.id,
        job_id=job_id,
        lines=body.lines,
        stream=body.stream,
    )
    await db.commit()
    return {"appended": count}
