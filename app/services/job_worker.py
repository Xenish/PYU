from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import JobStatus
from app.models.job import Job
from app.services.job_engine import start_job


async def process_next_job(db: AsyncSession) -> Optional[Job]:
    job = (
        await db.execute(
            select(Job).where(Job.status == JobStatus.QUEUED.value).order_by(Job.created_at).limit(1)
        )
    ).scalars().first()
    if not job:
        return None

    # lock marker
    job.locked_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    return await start_job(db, job)


async def run_worker_loop(db: AsyncSession, *, max_jobs: int | None = None) -> None:
    processed = 0
    while True:
        job = await process_next_job(db)
        if not job:
            break
        processed += 1
        if max_jobs is not None and processed >= max_jobs:
            break
