from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import App, Project, WebhookEndpoint
from fleetkit_api.schemas import WebhookCreate, WebhookOut
from fleetkit_api.services.jobs import PolicyDenied, enqueue_job

router = APIRouter(tags=["webhooks"])


def _signature_ok(secret: str, body: bytes, header: str | None) -> bool:
    """Accept legacy raw secret or `t=<ts>,v1=<hmac>` header."""
    if not header:
        return False
    if hmac.compare_digest(header, secret):
        return True
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    ts_raw, sig = parts.get("t"), parts.get("v1")
    if not ts_raw or not sig:
        return False
    try:
        ts = int(ts_raw)
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > 300:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def _to_out(endpoint: WebhookEndpoint) -> WebhookOut:
    return WebhookOut(
        id=endpoint.id,
        app_id=endpoint.app_id,
        name=endpoint.name,
        path_token=endpoint.path_token,
        secret=endpoint.secret,
        target_job_name=endpoint.target_job_name,
        is_enabled=endpoint.is_enabled,
        created_at=endpoint.created_at,
        ingest_path=f"/api/v1/hooks/{endpoint.path_token}",
    )


@router.get("/projects/{project_id}/webhooks", response_model=list[WebhookOut])
async def list_webhooks(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookOut]:
    result = await db.execute(
        select(WebhookEndpoint)
        .join(App, App.id == WebhookEndpoint.app_id)
        .where(App.project_id == project.id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return [_to_out(item) for item in result.scalars().all()]


@router.post(
    "/projects/{project_id}/apps/{app_id}/webhooks",
    response_model=WebhookOut,
    status_code=201,
)
async def create_webhook(
    app_id: str,
    body: WebhookCreate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookOut:
    app = await db.get(App, app_id)
    if app is None or app.project_id != project.id:
        raise HTTPException(status_code=404, detail="App не найдено")
    endpoint = WebhookEndpoint(
        app_id=app.id,
        name=body.name,
        target_job_name=body.target_job_name,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return _to_out(endpoint)


@router.post("/hooks/{path_token}")
async def ingest_webhook(
    path_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_fleetkit_signature: str | None = Header(default=None, alias="X-FleetKit-Signature"),
) -> dict[str, Any]:
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.path_token == path_token,
            WebhookEndpoint.is_enabled.is_(True),
        )
    )
    endpoint = result.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook не найден")
    raw_body = await request.body()
    if not _signature_ok(endpoint.secret, raw_body, x_fleetkit_signature):
        raise HTTPException(status_code=401, detail="Подпись не совпала")

    app = await db.get(App, endpoint.app_id)
    if app is None or not app.is_enabled:
        raise HTTPException(status_code=404, detail="App выключено")

    try:
        import json

        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    try:
        job = await enqueue_job(
            db,
            app=app,
            name=endpoint.target_job_name,
            payload={"headers": dict(request.headers), "body": payload, "webhook_id": endpoint.id},
            queue="webhooks",
            tags=["webhook", endpoint.name],
        )
    except PolicyDenied as exc:
        raise HTTPException(status_code=409, detail=f"policy denied: {exc.reason}") from exc
    await db.commit()
    return {"ok": True, "job_id": job.id}
