import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import JobStatus, JobType, TaskStatus
from app.models.job import Job
from app.models.planning import Sprint
from app.models.project import Project
from app.services.task_generation import generate_draft_tasks_for_sprint
from app.services.task_refinement import refine_tasks_pass2_for_sprint
from app.services.task_split import refine_tasks_pass3_for_sprint
from app.services.llm_policy import LLMQuotaExceeded, LLMJobBudgetExceeded
from app.observability.logging import get_logger, set_context, clear_context
from app.observability import metrics


class InvalidJobTransition(Exception):
    pass


class UnsupportedJobTypeError(Exception):
    pass


class JobCancelled(Exception):
    """Raised when cancellation_requested is set while running."""


ALLOWED_JOB_TRANSITIONS = {
    JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
}


async def create_job_for_task_pipeline(
    db: AsyncSession,
    project: Project,
    sprint: Sprint,
    payload_dict: dict | None = None,
) -> Job:
    job = Job(
        project_id=project.id,
        sprint_id=sprint.id,
        type=JobType.TASK_PIPELINE_FOR_SPRINT.value,
        status=JobStatus.QUEUED.value,
        payload_json=json.dumps(payload_dict or {}),
        progress_pct=0,
    )
    db.add(job)
    await db.flush()
    await db.commit()
    await db.refresh(job)
    return job


async def _update_progress(db: AsyncSession, job: Job, pct: int, step: str | None) -> None:
    job.progress_pct = pct
    job.current_step = step
    await db.flush()
    await db.commit()
    await db.refresh(job)


async def _run_task_pipeline_for_sprint(db: AsyncSession, sprint: Sprint, job: Job) -> dict:
    # Pass 1
    await _update_progress(db, job, 10, "pass1")
    if job.cancellation_requested:
        raise JobCancelled()
    draft_tasks = await generate_draft_tasks_for_sprint(db, sprint, job_id=job.id)

    # Pass 2
    await _update_progress(db, job, 50, "pass2")
    if job.cancellation_requested:
        raise JobCancelled()
    refined = await refine_tasks_pass2_for_sprint(db, sprint, job_id=job.id)

    # Pass 3
    await _update_progress(db, job, 80, "pass3")
    if job.cancellation_requested:
        raise JobCancelled()
    fine = await refine_tasks_pass3_for_sprint(db, sprint.id, job_id=job.id)

    ready_for_dev = len([t for t in fine if t.status == TaskStatus.READY_FOR_DEV])
    summary = {
        "draft_tasks": len(draft_tasks),
        "refined_tasks": len(refined),
        "fine_tasks": len(fine),
        "ready_for_dev_tasks": ready_for_dev,
    }
    await _update_progress(db, job, 100, "completed")
    return summary


def _ensure_job_transition(job: Job, new_status: JobStatus) -> None:
    allowed = ALLOWED_JOB_TRANSITIONS.get(JobStatus(job.status), set())
    if new_status not in allowed:
        raise InvalidJobTransition(f"{job.status} -> {new_status} geçişi yasak")


async def start_job(db: AsyncSession, job: Job) -> Job:
    logger = get_logger("masper.job", component="worker")
    if job.cancellation_requested and job.status == JobStatus.QUEUED.value:
        job.status = JobStatus.CANCELLED.value
        job.finished_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(job)
        return job

    _ensure_job_transition(job, JobStatus.RUNNING)
    set_context(job_id=job.id, project_id=job.project_id, component="worker")
    job.status = JobStatus.RUNNING.value
    job.started_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    await db.refresh(job)
    metrics.jobs_in_progress.labels(type=job.type).inc()
    logger.info("job.started", extra={"job_id": job.id, "project_id": job.project_id, "type": job.type})

    try:
        if JobType(job.type) == JobType.TASK_PIPELINE_FOR_SPRINT:
            sprint = await db.get(Sprint, job.sprint_id)
            if not sprint:
                raise ValueError("Sprint not found for job")
            result = await _run_task_pipeline_for_sprint(db, sprint, job)
        else:
            raise UnsupportedJobTypeError(job.type)

        job.status = JobStatus.COMPLETED.value
        job.result_json = json.dumps(result)
        metrics.jobs_total.labels(type=job.type, status="completed").inc()
        logger.info("job.completed", extra={"job_id": job.id, "project_id": job.project_id})
    except JobCancelled:
        job.status = JobStatus.CANCELLED.value
        metrics.jobs_total.labels(type=job.type, status="cancelled").inc()
    except (LLMQuotaExceeded, LLMJobBudgetExceeded) as exc:
        job.status = JobStatus.FAILED.value
        job.error_message = str(exc)
        metrics.jobs_total.labels(type=job.type, status="failed").inc()
        logger.warning(
            "job.failed",
            extra={"job_id": job.id, "project_id": job.project_id, "error": str(exc)},
        )
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.FAILED.value
        job.error_message = str(exc)
        metrics.jobs_total.labels(type=job.type, status="failed").inc()
        logger.error(
            "job.failed",
            extra={"job_id": job.id, "project_id": job.project_id, "error": str(exc)},
        )
    finally:
        job.finished_at = datetime.now(timezone.utc)
        metrics.jobs_in_progress.labels(type=job.type).dec()
        await db.commit()
        await db.refresh(job)
        clear_context()
    return job
