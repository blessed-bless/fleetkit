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


@app.command("project-create")
def project_create(name: str, slug: str, description: str = "") -> None:
    row = _client().create_project(name, slug, description)
    console.print(f"created [cyan]{row['id']}[/cyan] {row['slug']}")


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
    tag: Optional[list[str]] = typer.Option(None, help="Repeatable job tag"),
) -> None:
    body = json.loads(payload) if payload else {"source": "cli"}
    job = _client().enqueue(project_id, app_id, name, body, tags=tag or [])
    console.print(f"queued [cyan]{job['id']}[/cyan] status={job['status']}")


@app.command()
def jobs(
    project_id: str,
    status: Optional[str] = typer.Option(None),
    tag: Optional[str] = typer.Option(None),
    q: Optional[str] = typer.Option(None),
) -> None:
    rows = _client().jobs(project_id, status=status, tag=tag, q=q)
    table = Table(title="Jobs")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Queue")
    table.add_column("Tags")
    for row in rows[:50]:
        tags = ",".join(row.get("tags") or [])
        table.add_row(row["id"], row["name"], row["status"], row["queue"], tags)
    console.print(table)


@app.command()
def cancel(project_id: str, job_id: str) -> None:
    data = _client().cancel_job(project_id, job_id)
    console.print(f"cancel -> {data.get('status')}")


@app.command()
def retry(project_id: str, job_id: str) -> None:
    data = _client().retry_job(project_id, job_id)
    console.print(f"retry -> {data.get('status')}")


@app.command()
def clone(project_id: str, job_id: str, name: str | None = None) -> None:
    data = _client().clone_job(project_id, job_id, name=name)
    console.print(f"clone -> {data.get('id')} status={data.get('status')}")


@app.command("set-priority")
def set_priority(project_id: str, job_id: str, priority: int) -> None:
    data = _client().set_job_priority(project_id, job_id, priority)
    console.print(f"priority -> {data.get('priority')}")


@app.command()
def deps(project_id: str, job_id: str) -> None:
    rows = _client().job_dependencies(project_id, job_id)
    if not rows:
        console.print("no dependencies")
        return
    table = Table(title="Dependencies")
    table.add_column("ID")
    table.add_column("Depends on")
    for row in rows:
        table.add_row(row["id"], row["depends_on_job_id"])
    console.print(table)


@app.command("add-dep")
def add_dep(project_id: str, job_id: str, depends_on_job_id: str) -> None:
    data = _client().add_job_dependency(project_id, job_id, depends_on_job_id)
    console.print(f"dep -> {data.get('id')}")


@app.command()
def chain(
    project_id: str,
    app_id: str,
    names: str = typer.Argument(..., help="Comma-separated job names"),
    queue: str = "default",
) -> None:
    parts = [n.strip() for n in names.split(",") if n.strip()]
    data = _client().enqueue_chain(project_id, app_id, parts, queue=queue)
    console.print(f"chain -> {data.get('count')} jobs: {', '.join(data.get('job_ids') or [])}")


@app.command()
def workers(project_id: str) -> None:
    rows = _client().workers(project_id)
    table = Table(title="Workers")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Host")
    for row in rows:
        table.add_row(row["id"], row["name"], row["status"], row.get("hostname") or "")
    console.print(table)


@app.command()
def drain(
    project_id: str,
    worker_id: str,
    resume: bool = typer.Option(False, help="Bring worker back online"),
) -> None:
    data = _client().drain_worker(project_id, worker_id, draining=not resume)
    console.print(f"worker {data['name']} -> {data['status']}")


@app.command()
def schedules(project_id: str) -> None:
    rows = _client().schedules(project_id)
    table = Table(title="Schedules")
    table.add_column("Name")
    table.add_column("Cron")
    table.add_column("Enabled")
    for row in rows:
        table.add_row(row["name"], row["cron"], str(row.get("is_enabled")))
    console.print(table)


@app.command()
def webhooks(project_id: str) -> None:
    rows = _client().webhooks(project_id)
    table = Table(title="Webhooks")
    table.add_column("Name")
    table.add_column("Job")
    table.add_column("Path")
    for row in rows:
        table.add_row(row["name"], row["target_job_name"], row.get("ingest_path") or "")
    console.print(table)


@app.command()
def health(project_id: str) -> None:
    rows = _client().health_checks(project_id)
    table = Table(title="Health checks")
    table.add_column("Name")
    table.add_column("Target")
    table.add_column("Status")
    for row in rows:
        table.add_row(row["name"], row.get("target") or "", row.get("last_status") or "")
    console.print(table)


@app.command("health-run")
def health_run(project_id: str, check_id: str) -> None:
    data = _client().run_health(project_id, check_id)
    console.print(f"{data.get('name')} -> {data.get('last_status')}")


@app.command()
def templates(project_id: str) -> None:
    rows = _client().templates(project_id)
    table = Table(title="Templates")
    table.add_column("Slug")
    table.add_column("Job")
    table.add_column("Queue")
    for row in rows:
        table.add_row(row["slug"], row["job_name"], row["queue"])
    console.print(table)


@app.command("template-run")
def template_run(project_id: str, template_id: str) -> None:
    data = _client().run_template(project_id, template_id)
    console.print(data)


@app.command()
def quotas(project_id: str) -> None:
    console.print_json(data=_client().quotas(project_id))


@app.command("export")
def export_cfg(project_id: str, out: Optional[Path] = typer.Option(None)) -> None:
    data = _client().export_project(project_id)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if out:
        out.write_text(text, encoding="utf-8")
        console.print(f"wrote {out}")
    else:
        console.print(text)


@app.command()
def secrets(project_id: str) -> None:
    rows = _client().secrets(project_id)
    table = Table(title="Secrets")
    table.add_column("Name")
    table.add_column("Description")
    for row in rows:
        table.add_row(row["name"], row.get("description") or "")
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
