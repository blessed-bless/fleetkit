"""Named demo scenarios for local playground / docs screenshots."""

from __future__ import annotations

from typing import Any

SCENARIOS: dict[str, dict[str, Any]] = {}


def _add(name: str, **kwargs: Any) -> None:
    SCENARIOS[name] = {"name": name, **kwargs}


_add(
    "solo-bot",
    description="One Telegram bot + ping schedule",
    apps=[{"slug": "tg-bot", "kind": "bot"}, {"slug": "worker", "kind": "worker"}],
    schedules=[{"app": "worker", "cron": "*/5 * * * *", "job": "cron.heartbeat"}],
    alert_rules=[{"expression": "workers.offline>0", "severity": "warning"}],
)
_add(
    "webhook-shop",
    description="Inbound order webhooks into a worker queue",
    apps=[{"slug": "orders", "kind": "webhook"}, {"slug": "fulfillment", "kind": "worker"}],
    templates=[{"slug": "paid", "job_name": "webhook.received"}],
)
_add(
    "parser-fleet",
    description="Many HTTP fetch jobs with DLQ replay",
    apps=[{"slug": "parser", "kind": "worker"}],
    jobs=[{"name": "http.fetch", "payload": {"url": "https://example.com"}} for _ in range(20)],
)
_add(
    "observability-lab",
    description="Metrics + alerts + retention focused",
    apps=[{"slug": "lab", "kind": "worker"}],
    alert_rules=[
        {"expression": "queue.depth>50", "severity": "warning"},
        {"expression": "jobs.failed_rate>0.2", "severity": "critical"},
    ],
    retention={"job_logs": 7, "metrics": 14, "events": 21},
)

# Expand catalog so local demos have plenty of named setups.
for i in range(1, 31):
    _add(
        f"scenario-{i:02d}",
        description=f"Generated playground scenario {i}",
        apps=[{"slug": f"app-{i:02d}", "kind": "worker"}],
        jobs=[{"name": "ping", "payload": {"n": n}} for n in range(1, 6)],
        flags={f"flag_{i}": i % 2 == 0},
    )


def list_scenarios() -> list[str]:
    return sorted(SCENARIOS)


def get_scenario(name: str) -> dict[str, Any]:
    if name not in SCENARIOS:
        raise KeyError(name)
    return SCENARIOS[name]


def scenario_summary() -> list[dict[str, str]]:
    return [
        {"name": s["name"], "description": str(s.get("description", ""))}
        for s in SCENARIOS.values()
    ]
