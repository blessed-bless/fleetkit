from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import App, Job, JobStatus, Worker, WorkerStatus
from fleetkit_api.models_ext import (
    AlertFire,
    AlertRule,
    AlertSeverity,
    ChannelKind,
    NotificationChannel,
)

logger = logging.getLogger("fleetkit.alerts")

EXPR_RE = re.compile(
    r"^(?P<metric>jobs\.failed_rate|workers\.offline|queue\.depth|jobs\.running)"
    r"(?P<op>>=|<=|>|<|==)"
    r"(?P<value>\d+(?:\.\d+)?)$"
)


async def _metric_value(db: AsyncSession, project_id: str, metric: str) -> float:
    if metric == "workers.offline":
        value = await db.scalar(
            select(func.count())
            .select_from(Worker)
            .join(App, App.id == Worker.app_id)
            .where(App.project_id == project_id, Worker.status == WorkerStatus.offline)
        )
        return float(value or 0)
    if metric == "queue.depth":
        value = await db.scalar(
            select(func.count())
            .select_from(Job)
            .join(App, App.id == Job.app_id)
            .where(App.project_id == project_id, Job.status == JobStatus.queued)
        )
        return float(value or 0)
    if metric == "jobs.running":
        value = await db.scalar(
            select(func.count())
            .select_from(Job)
            .join(App, App.id == Job.app_id)
            .where(App.project_id == project_id, Job.status == JobStatus.running)
        )
        return float(value or 0)
    if metric == "jobs.failed_rate":
        since = datetime.now(UTC) - timedelta(hours=1)
        total = await db.scalar(
            select(func.count())
            .select_from(Job)
            .join(App, App.id == Job.app_id)
            .where(App.project_id == project_id, Job.created_at >= since)
        )
        failed = await db.scalar(
            select(func.count())
            .select_from(Job)
            .join(App, App.id == Job.app_id)
            .where(
                App.project_id == project_id,
                Job.status == JobStatus.failed,
                Job.finished_at >= since,
            )
        )
        total_f = float(total or 0)
        if total_f <= 0:
            return 0.0
        return float(failed or 0) / total_f
    return 0.0


def _compare(left: float, op: str, right: float) -> bool:
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    return left == right


async def _deliver(channel: NotificationChannel, message: str, payload: dict) -> bool:
    try:
        if channel.kind == ChannelKind.webhook:
            url = channel.config.get("url")
            if not url:
                return False
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={"message": message, "payload": payload})
                return resp.status_code < 300
        if channel.kind == ChannelKind.telegram:
            token = channel.config.get("bot_token")
            chat_id = channel.config.get("chat_id")
            if not token or not chat_id:
                return False
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": message},
                )
                return resp.status_code < 300
        if channel.kind == ChannelKind.email:
            # placeholder: log only; wire SMTP later
            logger.info("email alert to %s: %s", channel.config.get("to"), message)
            return True
    except Exception:
        logger.exception("alert delivery failed channel=%s", channel.id)
    return False


async def evaluate_project_alerts(db: AsyncSession, project_id: str) -> int:
    result = await db.execute(
        select(AlertRule).where(AlertRule.project_id == project_id, AlertRule.is_enabled.is_(True))
    )
    rules = list(result.scalars().all())
    fired = 0
    now = datetime.now(UTC)
    for rule in rules:
        match = EXPR_RE.match(rule.expression.strip())
        if not match:
            continue
        metric = match.group("metric")
        op = match.group("op")
        threshold = float(match.group("value"))
        current = await _metric_value(db, project_id, metric)
        if not _compare(current, op, threshold):
            continue
        if rule.last_fired_at and (now - rule.last_fired_at).total_seconds() < rule.cooldown_seconds:
            continue
        message = (
            f"[FleetKit:{rule.severity.value}] {rule.name}: {metric}={current} {op} {threshold}"
        )
        fire = AlertFire(
            project_id=project_id,
            rule_id=rule.id,
            severity=rule.severity,
            message=message,
            payload={"metric": metric, "value": current, "threshold": threshold},
        )
        if rule.channel_id:
            channel = await db.get(NotificationChannel, rule.channel_id)
            if channel and channel.is_enabled:
                fire.delivered = await _deliver(channel, message, fire.payload)
        db.add(fire)
        rule.last_fired_at = now
        fired += 1
    await db.flush()
    return fired


async def evaluate_all_alerts(db: AsyncSession) -> int:
    from fleetkit_api.models import Project

    projects = (await db.execute(select(Project.id))).scalars().all()
    total = 0
    for project_id in projects:
        total += await evaluate_project_alerts(db, project_id)
    return total


def parse_severity(raw: str) -> AlertSeverity:
    try:
        return AlertSeverity(raw)
    except ValueError:
        return AlertSeverity.warning
