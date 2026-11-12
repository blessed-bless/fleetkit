from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user, get_project_for_user
from fleetkit_api.models import ApiKey, Project, User, _api_key
from fleetkit_api.models_ext import ProjectMember
from fleetkit_api.schemas import ApiKeyCreate, ApiKeyOut, ProjectCreate, ProjectOut
from fleetkit_api.security import hash_api_key

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    member_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    result = await db.execute(
        select(Project)
        .where((Project.owner_id == user.id) | (Project.id.in_(member_ids)))
        .order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
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
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project: Project = Depends(get_project_for_user)) -> Project:
    return project


@router.get("/{project_id}/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    project: Project = Depends(get_project_for_user),
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
    project: Project = Depends(get_project_for_user),
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
