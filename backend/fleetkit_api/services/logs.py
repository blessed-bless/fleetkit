from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.models_ext import JobLogChunk


async def append_log(
    db: AsyncSession,
    *,
    project_id: str,
    job_id: str,
    line: str,
    stream: str = "stdout",
    seq: int | None = None,
) -> JobLogChunk:
    if seq is None:
        last = await db.scalar(
            select(JobLogChunk.seq)
            .where(JobLogChunk.job_id == job_id)
            .order_by(JobLogChunk.seq.desc())
            .limit(1)
        )
        seq = int(last or 0) + 1
    chunk = JobLogChunk(
        project_id=project_id,
        job_id=job_id,
        seq=seq,
        stream=stream,
        line=line[:8000],
    )
    db.add(chunk)
    await db.flush()
    return chunk


async def append_lines(
    db: AsyncSession,
    *,
    project_id: str,
    job_id: str,
    lines: list[str],
    stream: str = "stdout",
) -> int:
    count = 0
    for line in lines:
        if not line:
            continue
        await append_log(db, project_id=project_id, job_id=job_id, line=line, stream=stream)
        count += 1
    return count


async def read_logs(
    db: AsyncSession,
    *,
    job_id: str,
    after_seq: int = 0,
    limit: int = 500,
) -> list[JobLogChunk]:
    result = await db.execute(
        select(JobLogChunk)
        .where(JobLogChunk.job_id == job_id, JobLogChunk.seq > after_seq)
        .order_by(JobLogChunk.seq.asc())
        .limit(limit)
    )
    return list(result.scalars().all())
