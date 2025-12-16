from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.project import Project, ProjectStep
from app.models.planning import Epic, Sprint, Task, SprintPlan
from app.models.job import Job
from app.models.llm_usage import LLMUsage
from app.schemas.status import StatusOverview, ProjectDiagnostics, LLMInfo, LLMUpdate
from app.core.enums import JobStatus, JobType, TaskStatus
from app.core.config import get_settings

router = APIRouter()


@router.get("/status/overview", response_model=StatusOverview)
async def get_status_overview(db: AsyncSession = Depends(get_db)):
    projects_count = (
        await db.execute(
            select(func.count(Project.id)).where(Project.is_deleted == False)  # noqa: E712
        )
    ).scalar_one()
    jobs_counts = (
        await db.execute(select(Job.status, func.count(Job.id)).group_by(Job.status))
    ).all()
    jobs = {row[0]: row[1] for row in jobs_counts}
    today = date.today()
    llm_usage = (
        await db.execute(select(func.sum(LLMUsage.call_count)).where(LLMUsage.date == today))
    ).scalar()
    return StatusOverview(
        projects_count=projects_count,
        jobs=jobs,
        llm_calls_today=llm_usage or 0,
        llm_quota_limit=None,
    )


@router.get("/status/llm", response_model=LLMInfo)
async def get_llm_info():
    """
    Aktif LLM sağlayıcısı ve modelini döner.
    available_models listesi, UI'nin seçim için gösterebileceği bilinen modellerdir.
    """
    settings = get_settings()
    known_models = [
        settings.llm_model,
        "gpt-4.1-mini",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo",
        "dummy",
    ]
    available = list(dict.fromkeys(known_models))
    return LLMInfo(
        provider=settings.llm_provider,
        model=settings.llm_model,
        available_models=available,
    )


@router.post("/status/llm", response_model=LLMInfo)
async def set_llm(update: LLMUpdate):
    """
    Aktif LLM sağlayıcısı/modeli günceller ve yeni bilgiyi döner.
    Bu değerler uygulama ömrü boyunca geçerlidir; kalıcı ayar için .env dosyasını da güncelleyin.
    """
    settings = get_settings()
    if update.provider:
        settings.llm_provider = update.provider
    settings.llm_model = update.model
    known_models = [
        settings.llm_model,
        "gpt-4.1-mini",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo",
        "dummy",
    ]
    available = list(dict.fromkeys(known_models))
    return LLMInfo(
        provider=settings.llm_provider,
        model=settings.llm_model,
        available_models=available,
    )


@router.get("/projects/{project_id}/diagnostics", response_model=ProjectDiagnostics)
async def project_diagnostics(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    epic_count = (await db.execute(select(func.count(Epic.id)).where(Epic.project_id == project_id))).scalar_one()
    sprint_count = (
        await db.execute(
            select(func.count(Sprint.id)).join(SprintPlan, Sprint.sprint_plan_id == SprintPlan.id).where(SprintPlan.project_id == project_id)
        )
    ).scalar_one()
    tasks_counts = (
        await db.execute(
            select(Task.status, func.count(Task.id)).where(Task.project_id == project_id).group_by(Task.status)
        )
    ).all()
    tasks = {TaskStatus(row[0]).value: row[1] for row in tasks_counts}
    last_wizard = (
        await db.execute(
            select(func.max(ProjectStep.last_ai_run_at)).where(ProjectStep.project_id == project_id)
        )
    ).scalar()
    last_job = (
        await db.execute(
            select(Job.id, Job.status, Job.finished_at)
            .where(Job.project_id == project_id, Job.type == JobType.TASK_PIPELINE_FOR_SPRINT.value)
            .order_by(Job.finished_at.desc())
            .limit(1)
        )
    ).first()
    last_job_payload = None
    if last_job:
        last_job_payload = {"job_id": last_job.id, "status": last_job.status, "finished_at": last_job.finished_at}
    return ProjectDiagnostics(
        project_id=project_id,
        epic_count=epic_count,
        sprint_count=sprint_count,
        task_count=tasks,
        last_wizard_run_at=last_wizard,
        last_task_pipeline_job=last_job_payload,
    )
