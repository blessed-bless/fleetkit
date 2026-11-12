from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_for_user
from fleetkit_api.models import App, Project, WebhookEndpoint
from fleetkit_api.schemas import WebhookCreate, WebhookOut
from fleetkit_api.services.jobs import enqueue_job

router = APIRouter(tags=["webhooks"])


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
    if x_fleetkit_signature != endpoint.secret:
        raise HTTPException(status_code=401, detail="Подпись не совпала")

    app = await db.get(App, endpoint.app_id)
    if app is None or not app.is_enabled:
        raise HTTPException(status_code=404, detail="App выключено")

    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    job = await enqueue_job(
        db,
        app=app,
        name=endpoint.target_job_name,
        payload={"headers": dict(request.headers), "body": payload, "webhook_id": endpoint.id},
        queue="webhooks",
    )
    await db.commit()
    return {"ok": True, "job_id": job.id}
