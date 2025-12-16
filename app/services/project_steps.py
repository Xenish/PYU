from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import StepStatus, StepType
from app.db.filters import only_active
from app.models.project import ProjectStep


class InvalidStepTransition(Exception):
    """Geçersiz adım geçişi."""


ALLOWED_TRANSITIONS: dict[StepStatus, set[StepStatus]] = {
    StepStatus.PLANNED: {StepStatus.IN_PROGRESS, StepStatus.LOCKED, StepStatus.FAILED},
    StepStatus.IN_PROGRESS: {StepStatus.COMPLETED, StepStatus.FAILED},
    StepStatus.COMPLETED: {StepStatus.STALE},
    StepStatus.STALE: {StepStatus.IN_PROGRESS},
}


async def change_step_status(step: ProjectStep, new_status: StepStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(step.status, set())
    if new_status not in allowed:
        raise InvalidStepTransition(f"{step.status.value} -> {new_status.value} geçişi yasak")
    step.status = new_status


async def get_or_create_step(
    db: AsyncSession, project_id: int, step_type: StepType
) -> ProjectStep:
    stmt = only_active(select(ProjectStep), ProjectStep).where(
        ProjectStep.project_id == project_id, ProjectStep.step_type == step_type
    )
    result = await db.execute(stmt)
    step = result.scalars().first()
    if step:
        return step
    step = ProjectStep(
        project_id=project_id,
        step_type=step_type,
        status=StepStatus.PLANNED,
        created_at=datetime.now(timezone.utc),
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step
