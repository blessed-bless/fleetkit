from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.models import ApiKey, Project, User
from fleetkit_api.security import decode_access_token, hash_api_key
from fleetkit_api.security_suite.rbac import Permission
from fleetkit_api.services.membership import (
    ProjectAccess,
    assert_permission,
    resolve_project_access,
)

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


async def get_project_access(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectAccess:
    return await resolve_project_access(db, project_id=project_id, user=user)


async def get_project_for_user(
    access: ProjectAccess = Depends(get_project_access),
) -> Project:
    """Any project member (or owner). Use require_permission for write/sensitive routes."""
    return access.project


def require_permission(permission: Permission) -> Callable[..., Project]:
    async def _dep(access: ProjectAccess = Depends(get_project_access)) -> Project:
        assert_permission(access, permission)
        return access.project

    return _dep


def require_access(permission: Permission) -> Callable[..., ProjectAccess]:
    async def _dep(access: ProjectAccess = Depends(get_project_access)) -> ProjectAccess:
        assert_permission(access, permission)
        return access

    return _dep


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
