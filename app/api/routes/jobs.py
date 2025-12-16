from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.job import Job
from app.models.planning import Sprint
from app.models.project import Project
from app.schemas.jobs import JobCreateTaskPipeline, JobRead
from app.core.enums import JobStatus
from app.services.job_engine import create_job_for_task_pipeline, start_job
from app.services.job_worker import process_next_job

router = APIRouter()


async def _get_project_and_sprint(db: AsyncSession, project_id: int, sprint_id: int) -> tuple[Project, Sprint]:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    sprint = await db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return project, sprint


@router.post("/jobs/task-pipeline-for-sprint", response_model=JobRead)
async def create_task_pipeline_job(payload: JobCreateTaskPipeline, db: AsyncSession = Depends(get_db)):
    project, sprint = await _get_project_and_sprint(db, payload.project_id, payload.sprint_id)
    job = await create_job_for_task_pipeline(db, project, sprint, payload_dict=payload.model_dump())
    return job


@router.get("/jobs/{job_id}", response_model=JobRead)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/projects/{project_id}/jobs", response_model=list[JobRead])
async def list_jobs_for_project(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).where(Job.project_id == project_id).order_by(Job.created_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


@router.post("/jobs/{job_id}/cancel", response_model=JobRead)
async def cancel_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == JobStatus.COMPLETED.value or job.status == JobStatus.FAILED.value:
        raise HTTPException(status_code=409, detail="Job already finished")
    if job.status == JobStatus.QUEUED.value:
        job.status = JobStatus.CANCELLED.value
        job.finished_at = datetime.now(timezone.utc)
    else:
        job.cancellation_requested = True
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/jobs/run-next", response_model=JobRead | None)
async def run_next_job(db: AsyncSession = Depends(get_db)):
    # simple admin/test endpoint to kick worker once
    job = await process_next_job(db)
    return job
