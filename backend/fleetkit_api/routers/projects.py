from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user, require_access, require_permission
from fleetkit_api.models import ApiKey, Project, User, _api_key
from fleetkit_api.schemas import ApiKeyCreate, ApiKeyOut, ProjectCreate, ProjectOut
from fleetkit_api.security import hash_api_key
from fleetkit_api.security_suite.rbac import Permission
from fleetkit_api.services.membership import (
    ProjectAccess,
    ensure_owner_membership,
    list_accessible_projects,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectOut]:
    rows = await list_accessible_projects(db, user)
    return [
        ProjectOut(
            id=project.id,
            slug=project.slug,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            role=role.value,
        )
        for project, role in rows
    ]


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    existing = await db.execute(select(Project).where(Project.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug уже занят")
    project = Project(
        owner_id=user.id,
        slug=body.slug,
        name=body.name,
        description=body.description,
    )
    db.add(project)
    await db.flush()
    await ensure_owner_membership(db, project_id=project.id, user_id=user.id)
    await db.commit()
    await db.refresh(project)
    return ProjectOut(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        role="owner",
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    access: ProjectAccess = Depends(require_access(Permission.project_read)),
) -> ProjectOut:
    project = access.project
    return ProjectOut(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        role=access.role.value,
    )


@router.get("/{project_id}/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    project: Project = Depends(require_permission(Permission.project_write)),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyOut]:
    result = await db.execute(
        select(ApiKey).where(ApiKey.project_id == project.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyOut(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            raw_hint=k.raw_hint,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            secret=None,
        )
        for k in keys
    ]


@router.post("/{project_id}/api-keys", response_model=ApiKeyOut, status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    project: Project = Depends(require_permission(Permission.project_write)),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyOut:
    raw = _api_key()
    key = ApiKey(
        project_id=project.id,
        name=body.name,
        key_prefix=raw[:10],
        key_hash=hash_api_key(raw),
        raw_hint=raw[-4:],
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return ApiKeyOut(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        raw_hint=key.raw_hint,
        is_active=key.is_active,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        secret=raw,
    )
