from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import Project
from fleetkit_api.services.quotas import quota_snapshot

router = APIRouter(tags=["quotas"])


@router.get("/projects/{project_id}/quotas")
async def get_quotas(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await quota_snapshot(db, project.id)
