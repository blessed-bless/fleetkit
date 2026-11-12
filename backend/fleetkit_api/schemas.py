from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from fleetkit_api.models import JobStatus, WorkerStatus


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    description: str = ""


class ProjectOut(BaseModel):
    id: str
    slug: str
    name: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    raw_hint: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    # only present on create
    secret: str | None = None

    model_config = {"from_attributes": True}


class AppCreate(BaseModel):
    name: str
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")
    kind: str = "worker"
    config: dict[str, Any] = Field(default_factory=dict)


class AppUpdate(BaseModel):
    name: str | None = None
    is_enabled: bool | None = None
    config: dict[str, Any] | None = None


class AppOut(BaseModel):
    id: str
    project_id: str
    slug: str
    name: str
    kind: str
    config: dict[str, Any]
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkerRegisterIn(BaseModel):
    name: str
    hostname: str = ""
    labels: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


class WorkerHeartbeatIn(BaseModel):
    status: WorkerStatus = WorkerStatus.online
    meta: dict[str, Any] = Field(default_factory=dict)


class WorkerOut(BaseModel):
    id: str
    app_id: str
    name: str
    hostname: str
    status: WorkerStatus
    labels: dict[str, Any]
    last_heartbeat_at: datetime | None
    created_at: datetime
    meta: dict[str, Any]

    model_config = {"from_attributes": True}


class JobCreate(BaseModel):
    name: str
    queue: str = "default"
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=20)
    timeout_seconds: int = Field(default=300, ge=5, le=86400)
    scheduled_for: datetime | None = None


class JobCompleteIn(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)


class JobFailIn(BaseModel):
    error: str
    retry: bool = True


class JobOut(BaseModel):
    id: str
    app_id: str
    worker_id: str | None
    queue: str
    name: str
    status: JobStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    attempt: int
    max_attempts: int
    timeout_seconds: int
    scheduled_for: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    name: str
    cron: str
    timezone: str = "UTC"
    payload: dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True


class ScheduleOut(BaseModel):
    id: str
    app_id: str
    name: str
    cron: str
    timezone: str
    payload: dict[str, Any]
    is_enabled: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookCreate(BaseModel):
    name: str
    target_job_name: str = "webhook.received"


class WebhookOut(BaseModel):
    id: str
    app_id: str
    name: str
    path_token: str
    secret: str
    target_job_name: str
    is_enabled: bool
    created_at: datetime
    ingest_path: str | None = None

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: str
    project_id: str
    app_id: str | None
    job_id: str | None
    level: str
    kind: str
    message: str
    data: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class OverviewOut(BaseModel):
    projects: int
    apps: int
    workers_online: int
    jobs_queued: int
    jobs_running: int
    jobs_failed_24h: int
    recent_events: list[EventOut]
