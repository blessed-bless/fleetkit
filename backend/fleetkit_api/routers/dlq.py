from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import Project
from fleetkit_api.models_ext import DeadLetter
from fleetkit_api.schemas_ext import DeadLetterOut
from fleetkit_api.services.dlq import (
    discard_dead_letter,
    list_dead_letters,
    requeue_dead_letter,
    requeue_dead_letters_bulk,
)

router = APIRouter(tags=["dlq"])


class DlqBulkIn(BaseModel):
    dlq_ids: list[str] = Field(min_length=1, max_length=100)


@router.get("/projects/{project_id}/dead-letters", response_model=list[DeadLetterOut])
async def get_dlq(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[DeadLetter]:
    return await list_dead_letters(db, project_id=project.id)


@router.post("/projects/{project_id}/dead-letters/{dlq_id}/requeue")
async def requeue(
    dlq_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    item = await db.get(DeadLetter, dlq_id)
    if item is None or item.project_id != project.id:
        raise HTTPException(status_code=404, detail="Dead letter не найден")
    try:
        job = await requeue_dead_letter(db, item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return {"job_id": job.id, "dlq_id": item.id}


@router.post("/projects/{project_id}/dead-letters/{dlq_id}/discard", response_model=DeadLetterOut)
async def discard(
    dlq_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> DeadLetter:
    item = await db.get(DeadLetter, dlq_id)
    if item is None or item.project_id != project.id:
        raise HTTPException(status_code=404, detail="Dead letter не найден")
    try:
        await discard_dead_letter(db, item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/projects/{project_id}/dead-letters/requeue-bulk")
async def requeue_bulk(
    body: DlqBulkIn,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items: list[DeadLetter] = []
    for dlq_id in body.dlq_ids:
        item = await db.get(DeadLetter, dlq_id)
        if item is None or item.project_id != project.id:
            continue
        items.append(item)
    jobs = await requeue_dead_letters_bulk(db, items)
    await db.commit()
    return {"count": len(jobs), "job_ids": [j.id for j in jobs]}
