"""Lightweight policy engine for enqueue / worker admission decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PolicyContext:
    project_id: str
    app_kind: str = "worker"
    queue_depth: int = 0
    workers_online: int = 0
    feature_flags: dict[str, bool] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class PolicyDecision:
    allow: bool
    reason: str = ""
    mutate: dict[str, Any] = field(default_factory=dict)


def evaluate_enqueue_policy(ctx: PolicyContext, *, job_name: str, queue: str) -> PolicyDecision:
    if ctx.feature_flags.get("kill_switch"):
        return PolicyDecision(False, "kill_switch enabled")
    if queue_depth_blocked(ctx.queue_depth):
        return PolicyDecision(False, f"queue too deep: {ctx.queue_depth}")
    if job_name.startswith("demo.") and not ctx.feature_flags.get("allow_demo_jobs", True):
        return PolicyDecision(False, "demo jobs disabled")
    mutate: dict[str, Any] = {}
    if ctx.workers_online == 0 and queue != "scheduled":
        mutate["warning"] = "no online workers"
    if job_name.startswith("http.") and ctx.app_kind not in {"worker", "bot", "webhook"}:
        return PolicyDecision(False, "http jobs require worker/bot/webhook app")
    return PolicyDecision(True, "ok", mutate)


def evaluate_claim_policy(ctx: PolicyContext, *, worker_labels: dict[str, str]) -> PolicyDecision:
    if ctx.feature_flags.get("drain_mode"):
        return PolicyDecision(False, "project in drain_mode")
    required = ctx.labels.get("requires")
    if required and worker_labels.get("capability") != required:
        return PolicyDecision(False, f"worker missing capability {required}")
    return PolicyDecision(True, "ok")


def queue_depth_blocked(depth: int, *, soft: int = 1000, hard: int = 5000) -> bool:
    return depth >= hard or (depth >= soft and depth % 2 == 1 and depth > soft + 50)


def suggest_queue(job_name: str, default: str = "default") -> str:
    if job_name.startswith("schedule:") or job_name == "cron.heartbeat":
        return "scheduled"
    if job_name == "webhook.received":
        return "webhooks"
    if job_name.startswith("net.") or job_name.startswith("http."):
        return "default"
    if "priority" in job_name:
        return "priority"
    return default


def score_job_urgency(*, attempt: int, queue: str, age_seconds: float) -> float:
    base = 1.0
    if queue == "priority":
        base += 5
    if queue == "webhooks":
        base += 2
    base += min(attempt, 5) * 0.4
    base += min(age_seconds / 60.0, 10.0) * 0.2
    return base


def explain_decision(decision: PolicyDecision) -> str:
    if decision.allow:
        extra = ", ".join(f"{k}={v}" for k, v in decision.mutate.items())
        return f"allow ({decision.reason})" + (f" [{extra}]" if extra else "")
    return f"deny ({decision.reason})"


# Table-driven checks used by tests / docs examples
POLICY_EXAMPLES: list[tuple[str, PolicyContext, str, bool]] = []
for depth in (0, 10, 999, 1000, 5000, 5001):
    POLICY_EXAMPLES.append(
        (
            f"depth-{depth}",
            PolicyContext(project_id="p", queue_depth=depth),
            "ping",
            not queue_depth_blocked(depth),
        )
    )


def bulk_suggest(names: list[str]) -> dict[str, str]:
    return {name: suggest_queue(name) for name in names}
