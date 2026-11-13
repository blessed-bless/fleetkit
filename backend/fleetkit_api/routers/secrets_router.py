from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user, require_permission
from fleetkit_api.models import Project, User
from fleetkit_api.schemas_ext import SecretCreate, SecretMetaOut, SecretRevealOut
from fleetkit_api.security_suite.rbac import Permission
from fleetkit_api.services.audit import write_audit
from fleetkit_api.services.secrets import list_secrets, read_secret, upsert_secret

router = APIRouter(tags=["secrets"])


@router.get("/projects/{project_id}/secrets", response_model=list[SecretMetaOut])
async def secrets_list(
    project: Project = Depends(require_permission(Permission.secret_read)),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await list_secrets(db, project_id=project.id)


@router.put("/projects/{project_id}/secrets", response_model=SecretMetaOut)
async def secrets_upsert(
    body: SecretCreate,
    project: Project = Depends(require_permission(Permission.secret_write)),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await upsert_secret(
        db,
        project_id=project.id,
        name=body.name,
        value=body.value,
        description=body.description,
    )
    await write_audit(
        db,
        action="secret.upserted",
        project_id=project.id,
        actor_user_id=user.id,
        resource_type="secret",
        resource_id=row.id,
        data={"name": body.name},
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/projects/{project_id}/secrets/{name}/reveal", response_model=SecretRevealOut)
async def secrets_reveal(
    name: str,
    project: Project = Depends(require_permission(Permission.secret_reveal)),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SecretRevealOut:
    try:
        value = await read_secret(db, project_id=project.id, name=name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Секрет не найден") from exc
    await write_audit(
        db,
        action="secret.revealed",
        project_id=project.id,
        actor_user_id=user.id,
        resource_type="secret",
        data={"name": name},
    )
    await db.commit()
    return SecretRevealOut(name=name, value=value)
