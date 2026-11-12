from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Project, Schedule
from fleetkit_api.models_ext import (
    AlertRule,
    FeatureFlag,
    HealthCheck,
    JobTemplate,
    NotificationChannel,
    RetentionPolicy,
)


async def export_project(db: AsyncSession, project: Project) -> dict[str, Any]:
    apps = (
        await db.execute(select(App).where(App.project_id == project.id))
    ).scalars().all()
    schedules = (
        await db.execute(
            select(Schedule).join(App, App.id == Schedule.app_id).where(App.project_id == project.id)
        )
    ).scalars().all()
    channels = (
        await db.execute(
            select(NotificationChannel).where(NotificationChannel.project_id == project.id)
        )
    ).scalars().all()
    rules = (
        await db.execute(select(AlertRule).where(AlertRule.project_id == project.id))
    ).scalars().all()
    templates = (
        await db.execute(select(JobTemplate).where(JobTemplate.project_id == project.id))
    ).scalars().all()
    flags = (
        await db.execute(select(FeatureFlag).where(FeatureFlag.project_id == project.id))
    ).scalars().all()
    checks = (
        await db.execute(select(HealthCheck).where(HealthCheck.project_id == project.id))
    ).scalars().all()
    retention = (
        await db.execute(select(RetentionPolicy).where(RetentionPolicy.project_id == project.id))
    ).scalars().all()

    return {
        "version": 1,
        "project": {
            "slug": project.slug,
            "name": project.name,
            "description": project.description,
        },
        "apps": [
            {
                "slug": a.slug,
                "name": a.name,
                "kind": a.kind,
                "config": a.config,
                "is_enabled": a.is_enabled,
            }
            for a in apps
        ],
        "schedules": [
            {
                "app_slug": next((a.slug for a in apps if a.id == s.app_id), None),
                "name": s.name,
                "cron": s.cron,
                "timezone": s.timezone,
                "payload": s.payload,
                "is_enabled": s.is_enabled,
            }
            for s in schedules
        ],
        "channels": [
            {"name": c.name, "kind": c.kind.value, "config": c.config, "is_enabled": c.is_enabled}
            for c in channels
        ],
        "alert_rules": [
            {
                "name": r.name,
                "expression": r.expression,
                "severity": r.severity.value,
                "cooldown_seconds": r.cooldown_seconds,
                "is_enabled": r.is_enabled,
            }
            for r in rules
        ],
        "templates": [
            {
                "slug": t.slug,
                "name": t.name,
                "app_slug": next((a.slug for a in apps if a.id == t.app_id), None),
                "job_name": t.job_name,
                "queue": t.queue,
                "priority": t.priority,
                "payload": t.payload,
                "max_attempts": t.max_attempts,
                "timeout_seconds": t.timeout_seconds,
            }
            for t in templates
        ],
        "flags": [{"key": f.key, "enabled": f.enabled, "payload": f.payload} for f in flags],
        "health_checks": [
            {
                "name": h.name,
                "app_slug": next((a.slug for a in apps if a.id == h.app_id), None),
                "kind": h.kind,
                "target": h.target,
                "interval_seconds": h.interval_seconds,
                "timeout_seconds": h.timeout_seconds,
                "is_enabled": h.is_enabled,
            }
            for h in checks
        ],
        "retention": [
            {"kind": r.kind, "keep_days": r.keep_days, "is_enabled": r.is_enabled}
            for r in retention
        ],
    }


async def import_project_config(
    db: AsyncSession,
    project: Project,
    data: dict[str, Any],
    *,
    upsert_apps: bool = True,
) -> dict[str, int]:
    created = {"apps": 0, "schedules": 0, "flags": 0, "templates": 0}
    slug_to_app: dict[str, App] = {}
    existing_apps = (
        await db.execute(select(App).where(App.project_id == project.id))
    ).scalars().all()
    for app in existing_apps:
        slug_to_app[app.slug] = app

    for item in data.get("apps") or []:
        slug = item["slug"]
        if slug in slug_to_app:
            app = slug_to_app[slug]
            if upsert_apps:
                app.name = item.get("name", app.name)
                app.kind = item.get("kind", app.kind)
                app.config = item.get("config", app.config)
                app.is_enabled = item.get("is_enabled", app.is_enabled)
            continue
        app = App(
            project_id=project.id,
            slug=slug,
            name=item.get("name", slug),
            kind=item.get("kind", "worker"),
            config=item.get("config") or {},
            is_enabled=item.get("is_enabled", True),
        )
        db.add(app)
        await db.flush()
        slug_to_app[slug] = app
        created["apps"] += 1

    for item in data.get("schedules") or []:
        app = slug_to_app.get(item.get("app_slug") or "")
        if app is None:
            continue
        db.add(
            Schedule(
                app_id=app.id,
                name=item["name"],
                cron=item["cron"],
                timezone=item.get("timezone", "UTC"),
                payload=item.get("payload") or {},
                is_enabled=item.get("is_enabled", True),
            )
        )
        created["schedules"] += 1

    for item in data.get("flags") or []:
        existing = await db.scalar(
            select(FeatureFlag).where(
                FeatureFlag.project_id == project.id, FeatureFlag.key == item["key"]
            )
        )
        if existing:
            existing.enabled = item.get("enabled", False)
            existing.payload = item.get("payload") or {}
        else:
            db.add(
                FeatureFlag(
                    project_id=project.id,
                    key=item["key"],
                    enabled=item.get("enabled", False),
                    payload=item.get("payload") or {},
                )
            )
            created["flags"] += 1

    for item in data.get("templates") or []:
        app = slug_to_app.get(item.get("app_slug") or "")
        if app is None:
            continue
        existing = await db.scalar(
            select(JobTemplate).where(
                JobTemplate.project_id == project.id, JobTemplate.slug == item["slug"]
            )
        )
        if existing:
            continue
        db.add(
            JobTemplate(
                project_id=project.id,
                app_id=app.id,
                slug=item["slug"],
                name=item.get("name", item["slug"]),
                job_name=item.get("job_name", "ping"),
                queue=item.get("queue", "default"),
                priority=item.get("priority", 50),
                payload=item.get("payload") or {},
                max_attempts=item.get("max_attempts", 3),
                timeout_seconds=item.get("timeout_seconds", 300),
            )
        )
        created["templates"] += 1

    await db.flush()
    return created
