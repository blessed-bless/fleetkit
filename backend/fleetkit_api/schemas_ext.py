from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    name: str
    kind: str = "webhook"
    config: dict[str, Any] = Field(default_factory=dict)


class ChannelOut(BaseModel):
    id: str
    project_id: str
    name: str
    kind: str
    config: dict[str, Any]
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleCreate(BaseModel):
    name: str
    expression: str
    severity: str = "warning"
    channel_id: str | None = None
    cooldown_seconds: int = 300


class AlertRuleOut(BaseModel):
    id: str
    project_id: str
    name: str
    expression: str
    severity: str
    channel_id: str | None
    cooldown_seconds: int
    is_enabled: bool
    last_fired_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertFireOut(BaseModel):
    id: str
    rule_id: str
    severity: str
    message: str
    payload: dict[str, Any]
    delivered: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SecretCreate(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_\-\.]+$")
    value: str
    description: str = ""


class SecretMetaOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SecretRevealOut(BaseModel):
    name: str
    value: str


class LogLineIn(BaseModel):
    line: str
    stream: str = "stdout"
    seq: int | None = None


class LogBatchIn(BaseModel):
    lines: list[str]
    stream: str = "stdout"


class LogChunkOut(BaseModel):
    id: str
    job_id: str
    seq: int
    stream: str
    line: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DeadLetterOut(BaseModel):
    id: str
    app_id: str
    job_id: str
    job_name: str
    payload: dict[str, Any]
    error: str
    attempts: int
    requeued: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricIn(BaseModel):
    name: str
    value: float
    app_id: str | None = None
    labels: dict[str, Any] = Field(default_factory=dict)


class MetricOut(BaseModel):
    id: str
    name: str
    value: float
    labels: dict[str, Any]
    created_at: datetime
    app_id: str | None

    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    app_id: str
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")
    name: str
    job_name: str
    queue: str = "default"
    priority: int = 50
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = 3
    timeout_seconds: int = 300


class TemplateOut(BaseModel):
    id: str
    project_id: str
    app_id: str
    slug: str
    name: str
    job_name: str
    queue: str
    priority: int
    payload: dict[str, Any]
    max_attempts: int
    timeout_seconds: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditOut(BaseModel):
    id: str
    project_id: str | None
    actor_user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    data: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class RetentionOut(BaseModel):
    id: str
    kind: str
    keep_days: int
    is_enabled: bool

    model_config = {"from_attributes": True}


class RetentionUpdate(BaseModel):
    keep_days: int = Field(ge=1, le=3650)
    is_enabled: bool = True


class FlagCreate(BaseModel):
    key: str = Field(pattern=r"^[a-z0-9_\.\-]+$")
    enabled: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)


class FlagOut(BaseModel):
    id: str
    key: str
    enabled: bool
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthCheckCreate(BaseModel):
    app_id: str
    name: str
    kind: str = "http"
    target: str = ""
    interval_seconds: int = 60
    timeout_seconds: int = 10


class HealthCheckOut(BaseModel):
    id: str
    app_id: str
    name: str
    kind: str
    target: str
    interval_seconds: int
    timeout_seconds: int
    is_enabled: bool
    last_status: str
    last_checked_at: datetime | None
    last_error: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EnvVarCreate(BaseModel):
    key: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    value: str
    is_secret: bool = False


class EnvVarOut(BaseModel):
    id: str
    key: str
    is_secret: bool
    value_preview: str
    created_at: datetime


class MemberOut(BaseModel):
    id: str
    user_id: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteCreate(BaseModel):
    email: str
    role: str = "viewer"


class InviteOut(BaseModel):
    id: str
    email: str
    role: str
    token: str
    accepted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchJobCreate(BaseModel):
    app_id: str
    name: str
    payloads: list[dict[str, Any]]
    queue: str = "default"
    priority: int = 50


class SearchOut(BaseModel):
    apps: list[dict[str, Any]]
    jobs: list[dict[str, Any]]
    workers: list[dict[str, Any]]
    events: list[dict[str, Any]]
    dead_letters: list[dict[str, Any]]
