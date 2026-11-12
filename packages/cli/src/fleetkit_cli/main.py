from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from fleetkit_cli.client import CliClient

app = typer.Typer(help="FleetKit CLI — manage your automation control plane", no_args_is_help=True)
console = Console()
CONFIG_PATH = Path.home() / ".fleetkit" / "config.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _client() -> CliClient:
    cfg = _load_config()
    base = os.getenv("FLEETKIT_API_URL", cfg.get("base_url", "http://localhost:8000"))
    token = os.getenv("FLEETKIT_TOKEN", cfg.get("token"))
    return CliClient(base_url=base, token=token)


@app.command()
def login(
    email: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    base_url: str = typer.Option("http://localhost:8000"),
) -> None:
    """Save JWT for later commands."""
    client = CliClient(base_url=base_url)
    token = client.login(email, password)
    _save_config({"base_url": base_url, "token": token, "email": email})
    console.print(f"[green]Logged in as {email}[/green]")


@app.command()
def overview() -> None:
    data = _client().overview()
    table = Table(title="FleetKit overview")
    table.add_column("Metric")
    table.add_column("Value")
    for key in (
        "projects",
        "apps",
        "workers_online",
        "jobs_queued",
        "jobs_running",
        "jobs_failed_24h",
    ):
        table.add_row(key, str(data.get(key)))
    console.print(table)


@app.command("projects")
def list_projects() -> None:
    rows = _client().projects()
    table = Table(title="Projects")
    table.add_column("ID")
    table.add_column("Slug")
    table.add_column("Name")
    for row in rows:
        table.add_row(row["id"], row["slug"], row["name"])
    console.print(table)


@app.command()
def apps(project_id: str) -> None:
    rows = _client().apps(project_id)
    table = Table(title="Apps")
    table.add_column("ID")
    table.add_column("Slug")
    table.add_column("Kind")
    table.add_column("Enabled")
    for row in rows:
        table.add_row(row["id"], row["slug"], row["kind"], str(row["is_enabled"]))
    console.print(table)


@app.command()
def enqueue(
    project_id: str,
    app_id: str,
    name: str = "ping",
    payload: Optional[str] = typer.Option(None, help="JSON payload"),
) -> None:
    body = json.loads(payload) if payload else {"source": "cli"}
    job = _client().enqueue(project_id, app_id, name, body)
    console.print(f"queued [cyan]{job['id']}[/cyan] status={job['status']}")


@app.command()
def jobs(project_id: str) -> None:
    rows = _client().jobs(project_id)
    table = Table(title="Jobs")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Queue")
    for row in rows[:50]:
        table.add_row(row["id"], row["name"], row["status"], row["queue"])
    console.print(table)


@app.command()
def workers(project_id: str) -> None:
    rows = _client().workers(project_id)
    table = Table(title="Workers")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Host")
    for row in rows:
        table.add_row(row["name"], row["status"], row.get("hostname") or "")
    console.print(table)


@app.command()
def search(project_id: str, q: str) -> None:
    data = _client().search(project_id, q)
    console.print_json(data=data)


@app.command("dlq")
def dead_letters(project_id: str) -> None:
    rows = _client().dead_letters(project_id)
    table = Table(title="Dead letters")
    table.add_column("ID")
    table.add_column("Job")
    table.add_column("Error")
    for row in rows:
        table.add_row(row["id"], row["job_name"], (row.get("error") or "")[:80])
    console.print(table)


@app.command()
def requeue(project_id: str, dlq_id: str) -> None:
    data = _client().requeue(project_id, dlq_id)
    console.print(data)


@app.command()
def alerts(project_id: str) -> None:
    data = _client().evaluate_alerts(project_id)
    console.print(f"fired={data.get('fired')}")


@app.command()
def metrics(project_id: str) -> None:
    data = _client().snapshot_metrics(project_id)
    console.print_json(data=data)


if __name__ == "__main__":
    app()
