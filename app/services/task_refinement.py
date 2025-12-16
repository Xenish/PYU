from datetime import datetime, timezone
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PlanningDetailLevel, TaskGranularity
from app.models.planning import Sprint, Task, TaskDependency
from app.models.project import Project
from app.models.quality import DoDItem, NFRItem
from app.schemas.llm.tasks_refine import TaskRefinementResponse
from app.services.llm_adapter import call_llm
from app.services.prompts import build_task_refinement_prompt


async def refine_tasks_pass2_for_sprint(db: AsyncSession, sprint: Sprint, *, job_id: int | None = None) -> List[Task]:
    tasks = (
        await db.execute(
            select(Task).where(
                Task.sprint_id == sprint.id,
                Task.refinement_round == 1,
                Task.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    if not tasks:
        return []

    project_id = tasks[0].project_id
    detail_level = await db.scalar(
        select(Project.planning_detail_level).where(Project.id == project_id)
    ) or PlanningDetailLevel.NORMAL

    dod_items = (
        await db.execute(
            select(DoDItem).where(
                DoDItem.project_id == project_id, DoDItem.is_deleted == False  # noqa: E712
            )
        )
    ).scalars().all()
    nfr_items = (
        await db.execute(
            select(NFRItem).where(
                NFRItem.project_id == project_id, NFRItem.is_deleted == False  # noqa: E712
            )
        )
    ).scalars().all()

    prompt = build_task_refinement_prompt(tasks, dod_items, nfr_items, detail_level)
    response = await call_llm(
        prompt,
        TaskRefinementResponse,
        db=db,
        project_id=project_id,
        step_type="task_pass2",
        job_id=job_id,
        intent=None,
    )

    task_map = {t.id: t for t in tasks}
    task_ids = list(task_map.keys())

    # Clear previous dependencies for these tasks to avoid duplicates
    await db.execute(delete(TaskDependency).where(TaskDependency.task_id.in_(task_ids)))

    for item in response.tasks:
        task = task_map.get(item.task_id)
        if not task:
            continue
        task.title = item.title
        task.description = item.description
        task.acceptance_criteria = item.acceptance_criteria
        task.dod_focus = item.dod_focus
        task.nfr_focus = item.nfr_focus
        task.granularity = TaskGranularity.MEDIUM
        task.refinement_round = 2
        task.updated_at = datetime.now(timezone.utc)

        for dep_id in item.depends_on_task_ids or []:
            if dep_id == task.id:
                continue
            db.add(
                TaskDependency(
                    task_id=task.id,
                    depends_on_task_id=dep_id,
                )
            )

    await db.flush()
    await db.commit()
    refreshed = (
        await db.execute(select(Task).where(Task.id.in_(task_ids)))
    ).scalars().all()
    return refreshed
