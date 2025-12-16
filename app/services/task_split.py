from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from sqlalchemy import select, update

from app.core.enums import PlanningDetailLevel, TaskGranularity, TaskStatus
from app.models.planning import Task, TaskDependency
from app.models.project import Project
from app.schemas.llm.tasks_split import TaskSplitResponse
from app.services.llm_adapter import call_llm
from app.services.prompts import build_task_split_prompt


async def refine_tasks_pass3_for_sprint(db: AsyncSession, sprint_id: int, *, job_id: int | None = None) -> List[Task]:
    # Clean previous fine tasks to avoid accumulation on reruns
    await db.execute(
        update(Task)
        .where(
            Task.sprint_id == sprint_id,
            Task.refinement_round == 3,
            Task.granularity == TaskGranularity.FINE,
            Task.is_deleted == False,  # noqa: E712
        )
        .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
    )
    await db.execute(
        TaskDependency.__table__.delete().where(
            TaskDependency.depends_on_task_id.in_(
                select(Task.id).where(
                    Task.sprint_id == sprint_id,
                    Task.refinement_round == 3,
                    Task.is_deleted == True,  # noqa: E712
                )
            )
        )
    )
    medium_tasks = (
        await db.execute(
            select(Task).where(
                Task.sprint_id == sprint_id,
                Task.refinement_round == 2,
                Task.granularity == TaskGranularity.MEDIUM,
                Task.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    if not medium_tasks:
        return []

    project_id = medium_tasks[0].project_id
    detail_level = await db.scalar(
        select(Project.planning_detail_level).where(Project.id == project_id)
    ) or PlanningDetailLevel.NORMAL

    prompt = build_task_split_prompt(medium_tasks, detail_level)
    response = await call_llm(
        prompt,
        TaskSplitResponse,
        db=db,
        project_id=project_id,
        step_type="task_pass3",
        job_id=job_id,
        intent=None,
    )

    parent_map = {t.id: t for t in medium_tasks}
    max_order = (
        await db.scalar(
            select(Task.order_index)
            .where(Task.sprint_id == sprint_id)
            .order_by(Task.order_index.desc())
        )
    ) or 0
    new_tasks: list[Task] = []

    for idx, item in enumerate(response.tasks, start=1):
        parent = parent_map.get(item.parent_task_id)
        if not parent:
            continue
        child = Task(
            project_id=parent.project_id,
            sprint_id=parent.sprint_id,
            epic_id=parent.epic_id,
            parent_task_id=parent.id,
            title=item.title,
            description=item.description,
            acceptance_criteria=item.acceptance_criteria,
            estimate_sp=item.estimate_sp,
            dod_focus=parent.dod_focus,
            nfr_focus=parent.nfr_focus,
            status=TaskStatus.READY_FOR_DEV,
            granularity=TaskGranularity.FINE,
            refinement_round=3,
            order_index=max_order + idx,
            created_at=datetime.now(timezone.utc),
        )
        db.add(child)
        new_tasks.append(child)

    # parent tasks stale to signal replacement (reset stale->todo before we rerun)
    for parent in parent_map.values():
        if parent.status == TaskStatus.STALE:
            parent.status = TaskStatus.TODO

    # parent tasks stale to signal replacement
    for parent in parent_map.values():
        parent.status = TaskStatus.STALE
        parent.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.commit()
    refreshed = (
        await db.execute(
            select(Task).where(
                Task.sprint_id == sprint_id,
                Task.refinement_round == 3,
                Task.granularity == TaskGranularity.FINE,
                Task.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    return refreshed
