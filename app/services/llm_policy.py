from datetime import date
import asyncio
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.llm_usage import LLMUsage


class LLMQuotaExceeded(Exception):
    """Project bazlı günlük LLM limiti aşıldı."""


class LLMJobBudgetExceeded(Exception):
    """Job bazlı LLM çağrı limiti aşıldı."""


_job_call_counts: dict[int, int] = {}


async def check_and_increment_project_quota(
    db: AsyncSession,
    project_id: int,
    *,
    max_calls: int,
) -> None:
    today = date.today()
    usage = (
        await db.execute(
            select(LLMUsage).where(LLMUsage.project_id == project_id, LLMUsage.date == today)
        )
    ).scalars().first()
    if not usage:
        usage = LLMUsage(project_id=project_id, date=today, call_count=0)
        db.add(usage)
        await db.flush()
    if usage.call_count >= max_calls:
        raise LLMQuotaExceeded(f"Project {project_id} daily LLM quota exceeded")
    usage.call_count += 1
    await db.flush()
    await db.commit()


def check_job_budget(job_id: int | None, max_calls: int) -> None:
    if job_id is None:
        return
    count = _job_call_counts.get(job_id, 0)
    if count >= max_calls:
        raise LLMJobBudgetExceeded(f"Job {job_id} LLM call budget exceeded")
    _job_call_counts[job_id] = count + 1


async def backoff_sleep(attempt: int, initial: float, maximum: float) -> None:
    delay = min(initial * (2**attempt), maximum)
    jitter = delay * 0.1
    await asyncio.sleep(delay + random.uniform(-jitter, jitter))
