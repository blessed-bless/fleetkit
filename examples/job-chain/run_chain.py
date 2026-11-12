"""Enqueue a linear dependency chain via ManagementClient (SDK 0.3+).

Usage:
  set FLEETKIT_EMAIL / FLEETKIT_PASSWORD / FLEETKIT_BASE_URL
  set FLEETKIT_PROJECT_ID / FLEETKIT_APP_ID
  python run_chain.py
"""

from __future__ import annotations

import os
import sys

from fleetkit import ManagementClient


def main() -> int:
    base = os.environ.get("FLEETKIT_BASE_URL", "http://127.0.0.1:8000")
    email = os.environ.get("FLEETKIT_EMAIL", "admin@example.com")
    password = os.environ.get("FLEETKIT_PASSWORD", "fleetkit-admin")
    project_id = os.environ.get("FLEETKIT_PROJECT_ID")
    app_id = os.environ.get("FLEETKIT_APP_ID")
    if not project_id or not app_id:
        print("Need FLEETKIT_PROJECT_ID and FLEETKIT_APP_ID", file=sys.stderr)
        return 2

    client = ManagementClient.login(email, password, base_url=base)
    try:
        result = client.enqueue_chain(
            project_id,
            app_id,
            names=["demo.fetch", "demo.transform", "demo.publish"],
            payload={"source": "job-chain-example"},
            tags=["example", "chain"],
        )
        print(f"queued chain count={result.get('count')}")
        for job_id in result.get("job_ids") or []:
            print(f"  job {job_id}")
            deps = client.job_dependencies(project_id, job_id)
            if deps:
                print(f"    depends_on={[d['depends_on_job_id'] for d in deps]}")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
