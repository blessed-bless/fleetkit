from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.models import ApiKey, Project, User
from fleetkit_api.security import decode_access_token, hash_api_key

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется вход")
    try:
        payload = decode_access_token(creds.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен пустой")
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user


async def get_project_for_user(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Проект не найден")
    if project.owner_id == user.id:
        return project
    from fleetkit_api.models_ext import ProjectMember

    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project


async def require_project_admin(
    project: Project = Depends(get_project_for_user),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Owner or admin/operator member — for invites and membership writes."""
    if project.owner_id == user.id:
        return project
    from fleetkit_api.models_ext import ProjectMember

    member = await db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    if member is None or member.role not in {"owner", "admin", "operator"}:
        raise HTTPException(status_code=403, detail="Нужна роль admin/operator")
    return project


async def get_project_by_api_key(
    x_fleetkit_key: str | None = Header(default=None, alias="X-FleetKit-Key"),
    db: AsyncSession = Depends(get_db),
) -> Project:
    if not x_fleetkit_key:
        raise HTTPException(status_code=401, detail="Нужен заголовок X-FleetKit-Key")
    digest = hash_api_key(x_fleetkit_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == digest, ApiKey.is_active.is_(True)))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=401, detail="API-ключ неверный")
    api_key.last_used_at = datetime.now(UTC)
    project = await db.get(Project, api_key.project_id)
    if project is None:
        raise HTTPException(status_code=401, detail="Проект для ключа удалён")
    await db.commit()
    return project
