from __future__ import annotations

from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models import Job, JobStatus
from fleetkit_api.models_ext import JobDependency
from fleetkit_api.services.jobs import enqueue_job


class DependencyError(ValueError):
    """Invalid dependency edge (self-loop, missing job, or cycle)."""


async def _would_cycle(db: AsyncSession, *, job_id: str, depends_on_job_id: str) -> bool:
    if job_id == depends_on_job_id:
        return True
    frontier = [depends_on_job_id]
    seen: set[str] = set()
    while frontier:
        cur = frontier.pop()
        if cur == job_id:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        deps = (
            await db.execute(select(JobDependency).where(JobDependency.job_id == cur))
        ).scalars().all()
        for dep in deps:
            frontier.append(dep.depends_on_job_id)
    return False


async def add_dependency(
    db: AsyncSession,
    *,
    job_id: str,
    depends_on_job_id: str,
) -> JobDependency:
    if job_id == depends_on_job_id:
        raise DependencyError("job cannot depend on itself")
    child = await db.get(Job, job_id)
    parent = await db.get(Job, depends_on_job_id)
    if child is None or parent is None:
        raise DependencyError("job or dependency target missing")
    if child.app_id != parent.app_id:
        raise DependencyError("dependencies must stay inside the same app")
    existing = (
        await db.execute(
            select(JobDependency).where(
                JobDependency.job_id == job_id,
                JobDependency.depends_on_job_id == depends_on_job_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    if await _would_cycle(db, job_id=job_id, depends_on_job_id=depends_on_job_id):
        raise DependencyError("dependency would create a cycle")
    row = JobDependency(job_id=job_id, depends_on_job_id=depends_on_job_id)
    db.add(row)
    await db.flush()
    return row


async def list_dependencies(db: AsyncSession, job_id: str) -> list[JobDependency]:
    return list(
        (
            await db.execute(select(JobDependency).where(JobDependency.job_id == job_id))
        ).scalars().all()
    )


async def list_dependents(db: AsyncSession, job_id: str) -> list[JobDependency]:
    return list(
        (
            await db.execute(
                select(JobDependency).where(JobDependency.depends_on_job_id == job_id)
            )
        ).scalars().all()
    )


async def dependencies_satisfied(db: AsyncSession, job_id: str) -> bool:
    deps = await list_dependencies(db, job_id)
    if not deps:
        return True
    for dep in deps:
        parent = await db.get(Job, dep.depends_on_job_id)
        if parent is None or parent.status != JobStatus.succeeded:
            return False
    return True


async def blocked_job_ids(db: AsyncSession, job_ids: list[str]) -> set[str]:
    if not job_ids:
        return set()
    deps = (
        await db.execute(select(JobDependency).where(JobDependency.job_id.in_(job_ids)))
    ).scalars().all()
    if not deps:
        return set()
    parent_ids = {d.depends_on_job_id for d in deps}
    parents = (
        await db.execute(select(Job).where(Job.id.in_(list(parent_ids))))
    ).scalars().all()
    parent_status = {p.id: p.status for p in parents}
    by_job: dict[str, list[str]] = defaultdict(list)
    for dep in deps:
        by_job[dep.job_id].append(dep.depends_on_job_id)
    blocked: set[str] = set()
    for job_id, parents_for in by_job.items():
        for parent_id in parents_for:
            status = parent_status.get(parent_id)
            if status != JobStatus.succeeded:
                blocked.add(job_id)
                break
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
    queue: str = "default",
    tags: list[str] | None = None,
) -> list[str]:
    """Create a linear dependency chain of jobs."""
    if len(names) < 2:
        raise DependencyError("chain needs at least 2 job names")
    ids: list[str] = []
    prev: str | None = None
    for name in names:
        job = await enqueue_job(
            db,
            app=app,
            name=name,
            payload=payload or {},
            queue=queue,
            tags=tags,
        )
        if prev:
            await add_dependency(db, job_id=job.id, depends_on_job_id=prev)
        ids.append(job.id)
        prev = job.id
    return ids
