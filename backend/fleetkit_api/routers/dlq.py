from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import Project
from fleetkit_api.models_ext import DeadLetter
from fleetkit_api.schemas_ext import DeadLetterOut
from fleetkit_api.services.dlq import list_dead_letters, requeue_dead_letter

router = APIRouter(tags=["dlq"])


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
