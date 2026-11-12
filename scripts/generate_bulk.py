from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    recipes = ROOT / "docs" / "recipes"
    recipes.mkdir(parents=True, exist_ok=True)
    names = [
        ("telegram-alerts.md", "Telegram alerts", "Channel kind=telegram + rule workers.offline>0"),
        ("http-fetch-pipeline.md", "HTTP fetch pipeline", "Enqueue http.fetch and store sha256"),
        ("dead-letter-replay.md", "Dead letter replay", "Failed jobs land in DLQ; requeue from UI/CLI"),
        ("secret-vault.md", "Secret vault", "Store BOT_TOKEN via encrypted secrets API"),
        ("cron-heartbeat.md", "Cron heartbeat", "Schedule cron.heartbeat every 5 minutes"),
        ("batch-enqueue.md", "Batch enqueue", "POST /jobs/batch with up to 500 payloads"),
        ("health-checks.md", "Health checks", "HTTP and worker_heartbeat probes"),
        ("feature-flags.md", "Feature flags", "Toggle behavior per project without redeploy"),
        ("retention.md", "Retention policies", "Auto-delete old logs/events/metrics"),
        ("live-websocket.md", "Live websocket", "/api/v1/ws/projects/{id}?token=..."),
    ]
    for slug, title, body in names:
        (recipes / slug).write_text(
            f"# {title}\n\n{body}\n\n## Steps\n\n"
            "1. Create project API key\n2. Create app\n3. Configure resource\n"
            "4. Verify in dashboard\n\n",
            encoding="utf-8",
        )

    pkg = ROOT / "examples" / "recipes"
    pkg.mkdir(parents=True, exist_ok=True)
    for i in range(1, 26):
        (pkg / f"recipe_{i:02d}.py").write_text(
            f'''"""Recipe {i:02d}: sample automation sketch for FleetKit."""

from __future__ import annotations

import os

from fleetkit import FleetKit


def handle(job: dict) -> dict:
    name = job.get("name")
    payload = job.get("payload") or {{}}
    if name == "recipe.{i:02d}":
        return {{"recipe": {i}, "echo": payload}}
    return {{"ok": True, "recipe": {i}, "name": name}}


def main() -> None:
    api_key = os.environ["FLEETKIT_API_KEY"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    base = os.getenv("FLEETKIT_API_URL", "http://localhost:8000")
    with FleetKit(base_url=base, api_key=api_key) as fk:
        fk.run_loop(app_id=app_id, worker_name="recipe-{i:02d}", handler=handle)


if __name__ == "__main__":
    main()
''',
            encoding="utf-8",
        )
    print("generated recipes + examples")


if __name__ == "__main__":
    main()
