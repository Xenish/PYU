from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.models.project import Project, ProjectObjective
from app.schemas.llm.objective import ObjectiveLLMResponse
from app.services.llm_adapter import LLMError, call_llm
from app.services.project_steps import change_step_status, get_or_create_step
from app.services.prompts import build_objective_prompt


class ProjectNotFound(Exception):
    pass


async def run_objective_step(
    db: AsyncSession,
    project_id: int,
) -> List[ProjectObjective]:
    project = await db.get(Project, project_id)
    if not project:
        raise ProjectNotFound("Project not found")

    step = await get_or_create_step(db, project_id, StepType.OBJECTIVE)
    await _move_step_to_in_progress(step)

    await _soft_delete_unselected_objectives(db, project_id)
    selected_objs = await _get_selected_objectives(db, project_id)
    prompt = build_objective_prompt(project, selected_items=selected_objs)

    try:
        response = await call_llm(prompt, ObjectiveLLMResponse, db=db, project_id=project_id, step_type=StepType.OBJECTIVE.value)
    except LLMError:
        await db.rollback()
        raise

    # create objectives
    objs = []
    for item in response.objectives:
        obj = ProjectObjective(
            project_id=project_id,
            title=item.title,
            text=item.description,
            is_selected=False,
        )
        _apply_decision_support(obj, item)
        db.add(obj)
        objs.append(obj)
    await db.flush()
    await db.refresh(step)

    step.last_ai_run_at = datetime.now(timezone.utc)
    step.approval_status = ApprovalStatus.PENDING
    step.last_approved_at = None
    await change_step_status(step, StepStatus.COMPLETED)

    await db.commit()

    return objs


async def _list_objectives(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(ProjectObjective).where(
            ProjectObjective.project_id == project_id,
            ProjectObjective.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


async def _move_step_to_in_progress(step):
    if step.status == StepStatus.PLANNED:
        await change_step_status(step, StepStatus.IN_PROGRESS)
    elif step.status == StepStatus.COMPLETED:
        await change_step_status(step, StepStatus.STALE)
        await change_step_status(step, StepStatus.IN_PROGRESS)
    elif step.status == StepStatus.STALE:
        await change_step_status(step, StepStatus.IN_PROGRESS)
    else:
        # Already in progress or in a state that does not block regeneration
        return


async def _soft_delete_unselected_objectives(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(ProjectObjective).where(
            ProjectObjective.project_id == project_id,
            ProjectObjective.is_selected == False,  # noqa: E712
            ProjectObjective.is_deleted == False,  # noqa: E712
        )
    )
    unselected = result.scalars().all()
    for obj in unselected:
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def _get_selected_objectives(db: AsyncSession, project_id: int) -> List[ProjectObjective]:
    result = await db.execute(
        select(ProjectObjective).where(
            ProjectObjective.project_id == project_id,
            ProjectObjective.is_selected == True,  # noqa: E712
            ProjectObjective.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


def _apply_decision_support(model_obj, item):
    fields = [
        "priority_score",
        "impact_level",
        "recommendation_type",
        "category_tags",
        "rationale",
        "advantages",
        "disadvantages",
        "conflicts_with",
        "requires",
        "category_exclusive",
    ]
    for field in fields:
        if hasattr(model_obj, field):
            setattr(model_obj, field, getattr(item, field, getattr(model_obj, field, None)))
