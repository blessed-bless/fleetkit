"""Shared constants for FleetKit API."""

from __future__ import annotations

DEFAULT_QUEUES = ("default", "scheduled", "webhooks", "priority")

JOB_KINDS_DOCS = {
    "ping": "Health/connectivity probe",
    "http.fetch": "Generic HTTP fetch",
    "http.json": "GET JSON document",
    "system.info": "Worker runtime info",
    "util.sleep": "Artificial delay",
    "util.hash": "Hash helper",
    "webhook.received": "Created by webhook ingest",
}

ALERT_METRICS = (
    "jobs.failed_rate",
    "workers.offline",
    "queue.depth",
    "jobs.running",
)

RETENTION_KINDS = ("events", "job_logs", "metrics", "dead_letters", "jobs")

MEMBER_ROLES = ("owner", "admin", "operator", "viewer")

MAX_BATCH_JOBS = 500
MAX_LOG_LINE = 8000
AGENT_RATE_LIMIT_PER_MINUTE = 120
