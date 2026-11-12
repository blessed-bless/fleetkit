from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_project_by_api_key, get_project_for_user
from fleetkit_api.models import Project
from fleetkit_api.schemas_ext import MetricIn, MetricOut
from fleetkit_api.services.metrics import (
    outcome_totals,
    query_metrics,
    record_metric,
    snapshot_fleet_metrics,
)

router = APIRouter(tags=["metrics"])


@router.get("/projects/{project_id}/metrics", response_model=list[MetricOut])
async def get_metrics(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    name: str = Query(...),
    hours: int = Query(default=24, ge=1, le=168),
) -> list:
    return await query_metrics(db, project_id=project.id, name=name, hours=hours)


@router.get("/projects/{project_id}/metrics/outcomes")
async def get_outcomes(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=168),
) -> dict[str, float]:
    return await outcome_totals(db, project.id, hours=hours)


@router.post("/projects/{project_id}/metrics/snapshot")
async def snapshot(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, float]:
    values = await snapshot_fleet_metrics(db, project.id)
    await db.commit()
    return values


@router.post("/agent/metrics", response_model=MetricOut, status_code=201)
async def agent_metric(
    body: MetricIn,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    sample = await record_metric(
        db,
        project_id=project.id,
        name=body.name,
        value=body.value,
        app_id=body.app_id,
        labels=body.labels,
    )
    await db.commit()
    await db.refresh(sample)
    return sample
