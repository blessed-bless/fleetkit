from __future__ import annotations

from typing import Any

from fleetkit_api.models import App, Event, Job, Project, Schedule, Worker
from fleetkit_api.models_ext import AlertFire, AlertRule, DeadLetter, JobTemplate, MetricSample


def project_dict(p: Project) -> dict[str, Any]:
    return {
        "id": p.id,
        "slug": p.slug,
        "name": p.name,
        "description": p.description,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def app_dict(a: App) -> dict[str, Any]:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "slug": a.slug,
        "name": a.name,
        "kind": a.kind,
        "config": a.config,
        "is_enabled": a.is_enabled,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def job_dict(j: Job) -> dict[str, Any]:
    return {
        "id": j.id,
        "app_id": j.app_id,
        "worker_id": j.worker_id,
        "queue": j.queue,
        "name": j.name,
        "status": j.status.value if hasattr(j.status, "value") else j.status,
        "payload": j.payload,
        "tags": list(getattr(j, "tags", None) or []),
        "result": j.result,
        "error": j.error,
        "attempt": j.attempt,
        "max_attempts": j.max_attempts,
        "timeout_seconds": j.timeout_seconds,
        "scheduled_for": j.scheduled_for.isoformat() if j.scheduled_for else None,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        "created_at": j.created_at.isoformat() if j.created_at else None,
    }


def worker_dict(w: Worker) -> dict[str, Any]:
    return {
        "id": w.id,
        "app_id": w.app_id,
        "name": w.name,
        "hostname": w.hostname,
        "status": w.status.value if hasattr(w.status, "value") else w.status,
        "labels": w.labels,
        "last_heartbeat_at": w.last_heartbeat_at.isoformat() if w.last_heartbeat_at else None,
        "meta": w.meta,
        "created_at": w.created_at.isoformat() if w.created_at else None,
    }


def schedule_dict(s: Schedule) -> dict[str, Any]:
    return {
        "id": s.id,
        "app_id": s.app_id,
        "name": s.name,
        "cron": s.cron,
        "timezone": s.timezone,
        "payload": s.payload,
        "is_enabled": s.is_enabled,
        "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
        "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
    }


def event_dict(e: Event) -> dict[str, Any]:
    return {
        "id": e.id,
        "project_id": e.project_id,
        "app_id": e.app_id,
        "job_id": e.job_id,
        "level": e.level,
        "kind": e.kind,
        "message": e.message,
        "data": e.data,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def alert_rule_dict(r: AlertRule) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "expression": r.expression,
        "severity": r.severity.value,
        "channel_id": r.channel_id,
        "cooldown_seconds": r.cooldown_seconds,
        "is_enabled": r.is_enabled,
        "last_fired_at": r.last_fired_at.isoformat() if r.last_fired_at else None,
    }


def alert_fire_dict(f: AlertFire) -> dict[str, Any]:
    return {
        "id": f.id,
        "rule_id": f.rule_id,
        "severity": f.severity.value,
        "message": f.message,
        "payload": f.payload,
        "delivered": f.delivered,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def dead_letter_dict(d: DeadLetter) -> dict[str, Any]:
    return {
        "id": d.id,
        "app_id": d.app_id,
        "job_id": d.job_id,
        "job_name": d.job_name,
        "payload": d.payload,
        "error": d.error,
        "attempts": d.attempts,
        "requeued": d.requeued,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def metric_dict(m: MetricSample) -> dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "value": m.value,
        "labels": m.labels,
        "app_id": m.app_id,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def template_dict(t: JobTemplate) -> dict[str, Any]:
    return {
        "id": t.id,
        "slug": t.slug,
        "name": t.name,
        "app_id": t.app_id,
        "job_name": t.job_name,
        "queue": t.queue,
        "priority": t.priority,
        "payload": t.payload,
        "max_attempts": t.max_attempts,
        "timeout_seconds": t.timeout_seconds,
    }
