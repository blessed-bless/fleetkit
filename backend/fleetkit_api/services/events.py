from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import Event
from fleetkit_api.security_suite.redaction import redact_mapping, redact_text


async def emit_event(
    db: AsyncSession,
    *,
    project_id: str,
    kind: str,
    message: str,
    level: str = "info",
    app_id: str | None = None,
    job_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> Event:
    event = Event(
        project_id=project_id,
        app_id=app_id,
        job_id=job_id,
        level=level,
        kind=kind,
        message=redact_text(message)[:4000],
        data=redact_mapping(data or {}),
    )
    db.add(event)
    await db.flush()
    return event
