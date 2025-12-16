from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.services.epic_dependencies import topo_sort_epics, generate_epic_dependencies_for_project
from app.services.epic_generation import generate_epics_for_project
from app.services.story_points import estimate_story_points_for_epics
from app.services.sprint_quality import build_sprint_quality_summaries


async def create_sprint_plan_skeleton(
    db: AsyncSession,
    project: Project,
    *,
    num_sprints: int = 3,
) -> SprintPlan:
    # Ensure epics exist
    epics = (await db.execute(select(Epic).where(Epic.project_id == project.id))).scalars().all()
    if not epics:
        epics = await generate_epics_for_project(db, project)
    deps = await generate_epic_dependencies_for_project(db, project.id)

    ordered = topo_sort_epics(epics, deps)

    sprint_plan = SprintPlan(
        project_id=project.id,
        name="Sprint Plan",
        created_at=datetime.now(timezone.utc),
        approval_status=ApprovalStatus.PENDING,
        last_approved_at=None,
    )
    db.add(sprint_plan)
    await db.flush()

    sprints: List[Sprint] = []
    for idx in range(1, num_sprints + 1):
        sprint = Sprint(
            sprint_plan_id=sprint_plan.id,
            index=idx,
            name=f"Sprint {idx}",
            status="planned",
        )
        db.add(sprint)
        sprints.append(sprint)
    await db.flush()

    # round-robin distribute epics
    sprint_epics: list[SprintEpic] = []
    for i, epic in enumerate(ordered):
        target_sprint = sprints[i % num_sprints]
        se = SprintEpic(sprint_id=target_sprint.id, epic_id=epic.id, scope_note=None)
        db.add(se)
        sprint_epics.append(se)

    await db.commit()
    return sprint_plan


def _allocate_greedy(epics: list[Epic], sprints: list[Sprint]) -> tuple[list[SprintEpic], list[Epic]]:
    sprint_capacity_used = {s.id: 0 for s in sprints}
    assignments: list[SprintEpic] = []
    backlog: list[Epic] = []
    for epic in epics:
        sp = epic.story_points or 0
        placed = False
        for sprint in sprints:
            cap = sprint.capacity_sp or 0
            if sp == 0 or sprint_capacity_used[sprint.id] + sp <= cap:
                sprint_capacity_used[sprint.id] += sp
                assignments.append(SprintEpic(sprint_id=sprint.id, epic_id=epic.id, scope_note=None))
                placed = True
                break
        if not placed:
            backlog.append(epic)
    return assignments, backlog


async def create_capacity_aware_sprint_plan(
    db: AsyncSession,
    project: Project,
    *,
    num_sprints: int = 3,
    default_capacity_sp: int | None = None,
) -> tuple[SprintPlan, list[SprintEpic], list[Epic], dict]:
    # Ensure epics + deps
    epics = (await db.execute(select(Epic).where(Epic.project_id == project.id))).scalars().all()
    if not epics:
        epics = await generate_epics_for_project(db, project)
    await estimate_story_points_for_epics(db, project.id)
    deps = await generate_epic_dependencies_for_project(db, project.id)
    ordered = topo_sort_epics(epics, deps)

    sprint_plan = SprintPlan(
        project_id=project.id,
        name="Capacity Plan",
        created_at=datetime.now(timezone.utc),
        approval_status=ApprovalStatus.PENDING,
        last_approved_at=None,
    )
    db.add(sprint_plan)
    await db.flush()

    sprints: list[Sprint] = []
    for idx in range(1, num_sprints + 1):
        sprint = Sprint(
            sprint_plan_id=sprint_plan.id,
            index=idx,
            name=f"Sprint {idx}",
            status="planned",
            capacity_sp=default_capacity_sp,
        )
        db.add(sprint)
        sprints.append(sprint)
    await db.flush()

    assignments, backlog = _allocate_greedy(ordered, sprints)
    for se in assignments:
        db.add(se)
    await db.commit()
    quality = await build_sprint_quality_summaries(db, sprint_plan)
    return sprint_plan, assignments, backlog, quality
