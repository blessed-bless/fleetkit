from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user, get_project_for_user
from fleetkit_api.models import Project, User
from fleetkit_api.services.audit import write_audit
from fleetkit_api.services.export_import import export_project, import_project_config

router = APIRouter(tags=["transfer"])


@router.get("/projects/{project_id}/export")
async def export_cfg(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await export_project(db, project)


@router.post("/projects/{project_id}/import")
async def import_cfg(
    body: dict[str, Any],
    project: Project = Depends(get_project_for_user),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    created = await import_project_config(db, project, body)
    await write_audit(
        db,
        action="project.imported",
        project_id=project.id,
        actor_user_id=user.id,
        resource_type="project",
        resource_id=project.id,
        data=created,
    )
    await db.commit()
    return created
