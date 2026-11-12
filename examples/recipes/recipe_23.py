"""Recipe 23: sample automation sketch for FleetKit."""

from __future__ import annotations

import os

from fleetkit import FleetKit


def handle(job: dict) -> dict:
    name = job.get("name")
    payload = job.get("payload") or {}
    if name == "recipe.23":
        return {"recipe": 23, "echo": payload}
    return {"ok": True, "recipe": 23, "name": name}


def main() -> None:
    api_key = os.environ["FLEETKIT_API_KEY"]
    app_id = os.environ["FLEETKIT_APP_ID"]
    base = os.getenv("FLEETKIT_API_URL", "http://localhost:8000")
    with FleetKit(base_url=base, api_key=api_key) as fk:
        fk.run_loop(app_id=app_id, worker_name="recipe-23", handler=handle)


if __name__ == "__main__":
    main()
