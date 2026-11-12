from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.crypto_box import encrypt_text
from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user, get_project_for_user
from fleetkit_api.models import App, Project, User
from fleetkit_api.models_ext import (
    AppEnvVar,
    AuditEntry,
    FeatureFlag,
    HealthCheck,
    InviteToken,
    ProjectMember,
    RetentionPolicy,
)
from fleetkit_api.schemas_ext import (
    AuditOut,
    EnvVarCreate,
    EnvVarOut,
    FlagCreate,
    FlagOut,
    HealthCheckCreate,
    HealthCheckOut,
    InviteCreate,
    InviteOut,
    MemberOut,
    RetentionOut,
    RetentionUpdate,
    SearchOut,
)
from fleetkit_api.services.healthchecks import run_health_check
from fleetkit_api.services.retention import apply_retention, ensure_default_policies
from fleetkit_api.services.search import search_project

router = APIRouter(tags=["ops"])


@router.get("/projects/{project_id}/audit", response_model=list[AuditOut])
async def audit_list(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditEntry]:
    result = await db.execute(
        select(AuditEntry)
        .where(AuditEntry.project_id == project.id)
        .order_by(AuditEntry.created_at.desc())
        .limit(200)
    )
    return list(result.scalars().all())


@router.get("/projects/{project_id}/retention", response_model=list[RetentionOut])
async def retention_list(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[RetentionPolicy]:
    await ensure_default_policies(db, project.id)
    await db.commit()
    result = await db.execute(
        select(RetentionPolicy).where(RetentionPolicy.project_id == project.id)
    )
    return list(result.scalars().all())


@router.patch("/projects/{project_id}/retention/{kind}", response_model=RetentionOut)
async def retention_update(
    kind: str,
    body: RetentionUpdate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> RetentionPolicy:
    await ensure_default_policies(db, project.id)
    result = await db.execute(
        select(RetentionPolicy).where(
            RetentionPolicy.project_id == project.id, RetentionPolicy.kind == kind
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Политика не найдена")
    row.keep_days = body.keep_days
    row.is_enabled = body.is_enabled
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/projects/{project_id}/retention/run")
async def retention_run(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    deleted = await apply_retention(db, project.id)
    await db.commit()
    return deleted


@router.get("/projects/{project_id}/flags", response_model=list[FlagOut])
async def flags_list(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[FeatureFlag]:
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.project_id == project.id)
    )
    return list(result.scalars().all())


@router.put("/projects/{project_id}/flags", response_model=FlagOut)
async def flags_upsert(
    body: FlagCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlag:
    result = await db.execute(
        select(FeatureFlag).where(
            FeatureFlag.project_id == project.id, FeatureFlag.key == body.key
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = FeatureFlag(
            project_id=project.id,
            key=body.key,
            enabled=body.enabled,
            payload=body.payload,
        )
        db.add(row)
    else:
        row.enabled = body.enabled
        row.payload = body.payload
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/projects/{project_id}/health-checks", response_model=list[HealthCheckOut])
async def health_list(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[HealthCheck]:
    result = await db.execute(
        select(HealthCheck).where(HealthCheck.project_id == project.id)
    )
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/health-checks",
    response_model=HealthCheckOut,
    status_code=201,
)
async def health_create(
    body: HealthCheckCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> HealthCheck:
    app = await db.get(App, body.app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    row = HealthCheck(
        project_id=project.id,
        app_id=body.app_id,
        name=body.name,
        kind=body.kind,
        target=body.target,
        interval_seconds=body.interval_seconds,
        timeout_seconds=body.timeout_seconds,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/projects/{project_id}/health-checks/{check_id}/run", response_model=HealthCheckOut)
async def health_run(
    check_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> HealthCheck:
    row = await db.get(HealthCheck, check_id)
    if row is None or row.project_id != project.id:
        raise HTTPException(status_code=404, detail="Check не найден")
    await run_health_check(db, row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/projects/{project_id}/apps/{app_id}/env", response_model=list[EnvVarOut])
async def env_list(
    app_id: str,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[EnvVarOut]:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    rows = (
        await db.execute(select(AppEnvVar).where(AppEnvVar.app_id == app_id))
    ).scalars().all()
    out: list[EnvVarOut] = []
    for row in rows:
        preview = "***" if row.is_secret else "(set)"
        out.append(
            EnvVarOut(
                id=row.id,
                key=row.key,
                is_secret=row.is_secret,
                value_preview=preview,
                created_at=row.created_at,
            )
        )
    return out


@router.put("/projects/{project_id}/apps/{app_id}/env", response_model=EnvVarOut)
async def env_upsert(
    app_id: str,
    body: EnvVarCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> EnvVarOut:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    result = await db.execute(
        select(AppEnvVar).where(AppEnvVar.app_id == app_id, AppEnvVar.key == body.key)
    )
    row = result.scalar_one_or_none()
    blob, nonce = encrypt_text(body.value)
    if row is None:
        row = AppEnvVar(
            app_id=app_id,
            project_id=project.id,
            key=body.key,
            value_ciphertext=blob,
            value_nonce=nonce,
            is_secret=body.is_secret,
        )
        db.add(row)
    else:
        row.value_ciphertext = blob
        row.value_nonce = nonce
        row.is_secret = body.is_secret
    await db.commit()
    await db.refresh(row)
    return EnvVarOut(
        id=row.id,
        key=row.key,
        is_secret=row.is_secret,
        value_preview="***" if row.is_secret else "(set)",
        created_at=row.created_at,
    )


@router.get("/projects/{project_id}/members", response_model=list[MemberOut])
async def members_list(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectMember]:
    result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project.id)
    )
    return list(result.scalars().all())


@router.post("/projects/{project_id}/invites", response_model=InviteOut, status_code=201)
async def invite_create(
    body: InviteCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> InviteToken:
    row = InviteToken(
        project_id=project.id,
        email=body.email.lower(),
        role=body.role,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/projects/{project_id}/search", response_model=SearchOut)
async def search(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    q: str = Query(min_length=1),
) -> SearchOut:
    data = await search_project(db, project_id=project.id, q=q)
    return SearchOut(**data)


@router.get("/me/invites", response_model=list[InviteOut])
async def my_invites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InviteToken]:
    result = await db.execute(
        select(InviteToken).where(
            InviteToken.email == user.email.lower(),
            InviteToken.accepted.is_(False),
        )
    )
    return list(result.scalars().all())
