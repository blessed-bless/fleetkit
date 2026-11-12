from __future__ import annotations

from typing import Any, Literal, TypedDict


class WorkerDict(TypedDict, total=False):
    id: str
    app_id: str
    name: str
    hostname: str
    status: str
    labels: dict[str, Any]
    meta: dict[str, Any]


class JobDict(TypedDict, total=False):
    id: str
    app_id: str
    worker_id: str | None
    queue: str
    name: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    attempt: int
    max_attempts: int


JobStatusName = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    "timed_out",
]


class MetricPoint(TypedDict):
    name: str
    value: float
    labels: dict[str, Any]
