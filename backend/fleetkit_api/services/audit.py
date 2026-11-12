from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models_ext import AuditEntry


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    project_id: str | None = None,
    actor_user_id: str | None = None,
    resource_type: str = "",
    resource_id: str = "",
    ip: str = "",
    data: dict[str, Any] | None = None,
) -> AuditEntry:
    entry = AuditEntry(
        project_id=project_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip=ip,
        data=data or {},
    )
    db.add(entry)
    await db.flush()
    return entry
