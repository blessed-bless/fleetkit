from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import Project
from fleetkit_api.models_ext import (
    AlertFire,
    AlertRule,
    ChannelKind,
    NotificationChannel,
)
from fleetkit_api.schemas_ext import (
    AlertFireOut,
    AlertRuleCreate,
    AlertRuleOut,
    ChannelCreate,
    ChannelOut,
)
from fleetkit_api.security_suite.redaction import redact_mapping
from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url
from fleetkit_api.services.alerts import evaluate_project_alerts, parse_severity
from fleetkit_api.services.audit import write_audit

router = APIRouter(tags=["alerts"])


def _channel_out(row: NotificationChannel) -> ChannelOut:
    return ChannelOut(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        kind=row.kind.value if hasattr(row.kind, "value") else str(row.kind),
        config=redact_mapping(row.config or {}),
        is_enabled=row.is_enabled,
        created_at=row.created_at,
    )


@router.get("/projects/{project_id}/channels", response_model=list[ChannelOut])
async def list_channels(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChannelOut]:
    result = await db.execute(
        select(NotificationChannel)
        .where(NotificationChannel.project_id == project.id)
        .order_by(NotificationChannel.created_at.desc())
    )
    return [_channel_out(row) for row in result.scalars().all()]


@router.post("/projects/{project_id}/channels", response_model=ChannelOut, status_code=201)
async def create_channel(
    body: ChannelCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> ChannelOut:
    try:
        kind = ChannelKind(body.kind)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Неизвестный тип канала") from exc
    if kind == ChannelKind.webhook:
        url = (body.config or {}).get("url")
        if not url:
            raise HTTPException(status_code=400, detail="Для webhook нужен config.url")
        try:
            assert_safe_url(str(url))
        except SSRFBlocked as exc:
            raise HTTPException(status_code=400, detail=f"URL отклонён: {exc}") from exc
    row = NotificationChannel(
        project_id=project.id,
        name=body.name,
        kind=kind,
        config=body.config,
    )
    db.add(row)
    await write_audit(
        db,
        action="channel.created",
        project_id=project.id,
        resource_type="channel",
        data={"name": body.name, "kind": body.kind},
    )
    await db.commit()
    await db.refresh(row)
    return _channel_out(row)


@router.get("/projects/{project_id}/alert-rules", response_model=list[AlertRuleOut])
async def list_rules(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertRule]:
    result = await db.execute(
        select(AlertRule).where(AlertRule.project_id == project.id).order_by(AlertRule.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/projects/{project_id}/alert-rules", response_model=AlertRuleOut, status_code=201)
async def create_rule(
    body: AlertRuleCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> AlertRule:
    rule = AlertRule(
        project_id=project.id,
        name=body.name,
        expression=body.expression,
        severity=parse_severity(body.severity),
        channel_id=body.channel_id,
        cooldown_seconds=body.cooldown_seconds,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/projects/{project_id}/alert-fires", response_model=list[AlertFireOut])
async def list_fires(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertFire]:
    result = await db.execute(
        select(AlertFire)
        .where(AlertFire.project_id == project.id)
        .order_by(AlertFire.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.post("/projects/{project_id}/alerts/evaluate")
async def evaluate_now(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    fired = await evaluate_project_alerts(db, project.id)
    await db.commit()
    return {"fired": fired}
