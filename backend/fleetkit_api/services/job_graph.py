from __future__ import annotations

from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import Job, JobStatus
from fleetkit_api.models_ext import JobDependency
from fleetkit_api.services.jobs import enqueue_job


async def add_dependency(db: AsyncSession, *, job_id: str, depends_on_job_id: str) -> JobDependency:
    row = JobDependency(job_id=job_id, depends_on_job_id=depends_on_job_id)
    db.add(row)
    await db.flush()
    return row


async def dependencies_satisfied(db: AsyncSession, job_id: str) -> bool:
    deps = (
        await db.execute(select(JobDependency).where(JobDependency.job_id == job_id))
    ).scalars().all()
    if not deps:
        return True
    for dep in deps:
        parent = await db.get(Job, dep.depends_on_job_id)
        if parent is None or parent.status != JobStatus.succeeded:
            return False
    return True


async def blocked_job_ids(db: AsyncSession, job_ids: list[str]) -> set[str]:
    blocked: set[str] = set()
    for job_id in job_ids:
        if not await dependencies_satisfied(db, job_id):
            blocked.add(job_id)
    return blocked


def topological_layers(edges: list[tuple[str, str]]) -> list[list[str]]:
    """edges: (job, depends_on). Returns layers safe to run in parallel."""
    nodes: set[str] = set()
    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)
    for job_id, parent in edges:
        nodes.add(job_id)
        nodes.add(parent)
        incoming[job_id].add(parent)
        outgoing[parent].add(job_id)
    ready = deque([n for n in nodes if not incoming[n]])
    layers: list[list[str]] = []
    seen: set[str] = set()
    while ready:
        layer = list(ready)
        ready.clear()
        layers.append(layer)
        for node in layer:
            seen.add(node)
            for child in outgoing[node]:
                incoming[child].discard(node)
                if not incoming[child] and child not in seen:
                    ready.append(child)
    return layers


async def enqueue_chain(
    db: AsyncSession,
    *,
    app,
    names: list[str],
    payload: dict | None = None,
) -> list[str]:
    """Create a linear dependency chain of jobs."""
    ids: list[str] = []
    prev: str | None = None
    for name in names:
        job = await enqueue_job(db, app=app, name=name, payload=payload or {})
        if prev:
            await add_dependency(db, job_id=job.id, depends_on_job_id=prev)
        ids.append(job.id)
        prev = job.id
    return ids
