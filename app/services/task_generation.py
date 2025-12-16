from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TaskGranularity, TaskStatus, PlanningDetailLevel
from app.models.planning import Epic, Sprint, SprintEpic, Task
from app.schemas.llm.tasks import TaskDraftResponse
from app.services.llm_adapter import call_llm
from app.services.prompts import build_task_draft_prompt


async def generate_draft_tasks_for_epic(
    db: AsyncSession, epic: Epic, sprint: Sprint, *, job_id: int | None = None
) -> List[Task]:
    detail_level = PlanningDetailLevel.LOW
    prompt = build_task_draft_prompt(epic, sprint, detail_level=detail_level)
    response = await call_llm(
        prompt,
        TaskDraftResponse,
        db=db,
        project_id=epic.project_id,
        step_type="task_pass1",
        job_id=job_id,
        intent=None,
    )
    tasks: list[Task] = []
    base_index = (
        await db.scalar(
            select(Task.order_index)
            .where(Task.sprint_id == sprint.id)
            .order_by(Task.order_index.desc())
        )
    ) or 0

    for i, item in enumerate(response.tasks, start=1):
        task = Task(
            project_id=epic.project_id,
            sprint_id=sprint.id,
            epic_id=epic.id,
            title=item.title,
            description=item.description,
            status=TaskStatus.TODO,
            granularity=TaskGranularity.COARSE,
            refinement_round=1,
            order_index=base_index + i,
            created_at=datetime.now(timezone.utc),
        )
        db.add(task)
        tasks.append(task)
    await db.flush()
    await db.commit()
    return tasks


async def generate_draft_tasks_for_sprint(
    db: AsyncSession, sprint: Sprint, *, job_id: int | None = None
) -> List[Task]:
    sprint_epics = (
        await db.execute(
            select(SprintEpic).where(SprintEpic.sprint_id == sprint.id)
        )
    ).scalars().all()
    epic_ids = [se.epic_id for se in sprint_epics]
    epics = (
        await db.execute(select(Epic).where(Epic.id.in_(epic_ids)))
    ).scalars().all()
    tasks: list[Task] = []
    for epic in epics:
        tasks.extend(await generate_draft_tasks_for_epic(db, epic, sprint, job_id=job_id))
    return tasks
