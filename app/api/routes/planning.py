from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps.spec_lock import ensure_project_unlocked
from sqlalchemy import select
from app.models.planning import Epic, EpicDependency, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.schemas.planning import (
    EpicDependencyRead,
    EpicRead,
    PlanningEpicOverview,
    PlanningOverview,
    PlanningSprintOverview,
    SprintEpicRead,
    SprintPlanRead,
    SprintRead,
)
from app.services.epic_dependencies import generate_epic_dependencies_for_project
from app.services.epic_generation import generate_epics_for_project
from app.services.sprint_planning import (
    create_sprint_plan_skeleton,
    create_capacity_aware_sprint_plan,
)
from app.services.story_points import estimate_story_points_for_epics
from app.services.sprint_quality import build_sprint_quality_summaries

router = APIRouter()


async def _get_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/planning/generate-epics")
async def generate_epics(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    project = await _get_project(db, project_id)
    epics = await generate_epics_for_project(db, project)
    deps = await generate_epic_dependencies_for_project(db, project.id)
    return {
        "epics": [EpicRead.model_validate(e) for e in epics],
        "dependencies": [EpicDependencyRead.model_validate(d) for d in deps],
    }


@router.post("/projects/{project_id}/planning/estimate-epic-story-points")
async def estimate_story_points(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    project = await _get_project(db, project_id)
    epics = await estimate_story_points_for_epics(db, project.id)
    return {"epics": [EpicRead.model_validate(e) for e in epics]}


@router.post("/projects/{project_id}/planning/generate-capacity-plan")
async def generate_capacity_plan(
    project_id: int,
    num_sprints: int = 3,
    default_capacity_sp: int | None = None,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    project = await _get_project(db, project_id)
    sprint_plan, assignments, backlog, quality = await create_capacity_aware_sprint_plan(
        db, project, num_sprints=num_sprints, default_capacity_sp=default_capacity_sp
    )
    sprints = (
        await db.execute(select(Sprint).where(Sprint.sprint_plan_id == sprint_plan.id))
    ).scalars().all()
    return {
        "sprint_plan": SprintPlanRead.model_validate(sprint_plan),
        "sprints": [SprintRead.model_validate(s) for s in sprints],
        "sprint_epics": [SprintEpicRead.model_validate(se) for se in assignments],
        "unscheduled_epics": [EpicRead.model_validate(e) for e in backlog],
        "quality_summary": quality,
    }


@router.post("/projects/{project_id}/planning/generate-sprint-plan")
async def generate_sprint_plan(
    project_id: int,
    num_sprints: int = 3,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    project = await _get_project(db, project_id)
    sprint_plan = await create_sprint_plan_skeleton(db, project, num_sprints=num_sprints)
    sprints = (
        await db.execute(select(Sprint).where(Sprint.sprint_plan_id == sprint_plan.id))
    ).scalars().all()
    sprint_ids = [s.id for s in sprints]
    sprint_epics = (
        await db.execute(select(SprintEpic).where(SprintEpic.sprint_id.in_(sprint_ids)))
    ).scalars().all()
    return {
        "sprint_plan": SprintPlanRead.model_validate(sprint_plan),
        "sprints": [SprintRead.model_validate(s) for s in sprints],
        "sprint_epics": [SprintEpicRead.model_validate(se) for se in sprint_epics],
    }


@router.get("/projects/{project_id}/planning/overview", response_model=PlanningOverview)
async def planning_overview(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await _get_project(db, project_id)

    # Always fetch epics, even if there's no sprint plan yet
    epics = (
        await db.execute(select(Epic).where(Epic.project_id == project.id))
    ).scalars().all()

    deps = (
        await db.execute(select(EpicDependency).where(EpicDependency.project_id == project.id))
    ).scalars().all()
    deps_map: dict[int, list[int]] = {}
    for dep in deps:
        deps_map.setdefault(dep.epic_id, []).append(dep.depends_on_epic_id)

    sprint_plan = (
        await db.execute(
            select(SprintPlan)
            .where(SprintPlan.project_id == project.id)
            .order_by(SprintPlan.id.desc())
            .limit(1)
        )
    ).scalars().first()

    if not sprint_plan:
        # Return epics without sprint assignments
        epic_payload = [
            PlanningEpicOverview(
                id=e.id,
                name=e.name,
                category=e.category,
                story_points=e.story_points,
                sprint_ids=[],
                dependencies=deps_map.get(e.id, []),
                quality_tags=[],
            )
            for e in epics
        ]
        return PlanningOverview(project_id=project.id, epics=epic_payload, sprints=[])

    sprints = (
        await db.execute(select(Sprint).where(Sprint.sprint_plan_id == sprint_plan.id))
    ).scalars().all()
    sprint_ids = [s.id for s in sprints]
    sprint_epics = (
        await db.execute(select(SprintEpic).where(SprintEpic.sprint_id.in_(sprint_ids)))
    ).scalars().all()

    epics_by_id = {e.id: e for e in epics}

    epic_to_sprints: dict[int, list[int]] = {}
    for se in sprint_epics:
        epic_to_sprints.setdefault(se.epic_id, []).append(se.sprint_id)

    quality = await build_sprint_quality_summaries(db, sprint_plan)

    allocated: dict[int, int] = {sid: 0 for sid in sprint_ids}
    for se in sprint_epics:
        epic = epics_by_id.get(se.epic_id)
        if not epic:
            continue
        allocated[se.sprint_id] = allocated.get(se.sprint_id, 0) + (epic.story_points or 0)

    epic_payload = [
        PlanningEpicOverview(
            id=e.id,
            name=e.name,
            category=e.category,
            story_points=e.story_points,
            sprint_ids=epic_to_sprints.get(e.id, []),
            dependencies=deps_map.get(e.id, []),
            quality_tags=[],
        )
        for e in epics
    ]

    sprint_payload = [
        PlanningSprintOverview(
            id=s.id,
            name=s.name,
            capacity_sp=s.capacity_sp,
            allocated_sp=allocated.get(s.id, 0),
            epic_ids=[se.epic_id for se in sprint_epics if se.sprint_id == s.id],
            quality_summary=quality.get(s.id, {"dod_count": 0, "nfr_categories": []}),
            start_date=None,
            end_date=None,
        )
        for s in sprints
    ]

    return PlanningOverview(project_id=project.id, epics=epic_payload, sprints=sprint_payload)
