from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.enums import TaskGranularity, TaskStatus
from app.models.planning import Sprint, Task, Epic
from app.schemas.planning import TaskRead, TaskStatusUpdate
from app.services.task_generation import generate_draft_tasks_for_sprint
from app.services.task_refinement import refine_tasks_pass2_for_sprint
from app.services.task_split import refine_tasks_pass3_for_sprint
from app.services.task_state import change_task_status, InvalidTaskTransition

router = APIRouter()


async def _get_sprint(db: AsyncSession, sprint_id: int) -> Sprint:
    sprint = await db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint


@router.post("/sprints/{sprint_id}/tasks/generate-draft", response_model=list[TaskRead])
async def generate_draft_tasks(sprint_id: int, db: AsyncSession = Depends(get_db)):
    sprint = await _get_sprint(db, sprint_id)
    tasks = await generate_draft_tasks_for_sprint(db, sprint)
    return tasks


@router.get("/sprints/{sprint_id}/tasks", response_model=list[TaskRead])
async def list_tasks(
    sprint_id: int,
    ready_for_dev_only: bool = Query(False, description="Sadece ready_for_dev fine task'leri döndür"),
    for_board: bool = Query(False, description="Task board için tüm statüleri döndür"),
    limit: int = Query(50, ge=1, le=200, description="Max rows"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: AsyncSession = Depends(get_db),
):
    sprint = await _get_sprint(db, sprint_id)
    stmt = select(Task).where(Task.sprint_id == sprint.id, Task.is_deleted == False)  # noqa: E712
    if ready_for_dev_only:
        stmt = stmt.where(
            Task.status == TaskStatus.READY_FOR_DEV,
            Task.granularity == TaskGranularity.FINE,
            Task.refinement_round == 3,
        )
    stmt = stmt.order_by(Task.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    if for_board:
        epic_ids = {t.epic_id for t in tasks if t.epic_id}
        epic_name_by_id = {}
        if epic_ids:
            epic_rows = await db.execute(select(Epic).where(Epic.id.in_(epic_ids)))
            epic_name_by_id = {e.id: e.name for e in epic_rows.scalars().all()}
        for t in tasks:
            if t.epic_id:
                t.epic_name = epic_name_by_id.get(t.epic_id)  # type: ignore[attr-defined]
    return tasks


@router.post("/sprints/{sprint_id}/tasks/refine-pass2", response_model=list[TaskRead])
async def refine_pass2(sprint_id: int, db: AsyncSession = Depends(get_db)):
    sprint = await _get_sprint(db, sprint_id)
    tasks = await refine_tasks_pass2_for_sprint(db, sprint)
    return tasks


@router.post("/sprints/{sprint_id}/tasks/refine-pass3", response_model=list[TaskRead])
async def refine_pass3(sprint_id: int, db: AsyncSession = Depends(get_db)):
    sprint = await _get_sprint(db, sprint_id)
    tasks = await refine_tasks_pass3_for_sprint(db, sprint.id)
    return tasks


@router.patch("/tasks/{task_id}/status", response_model=TaskRead)
async def update_task_status(
    task_id: int, payload: TaskStatusUpdate, db: AsyncSession = Depends(get_db)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        new_status = TaskStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")
    try:
        change_task_status(task, new_status)
    except InvalidTaskTransition as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await db.commit()
    await db.refresh(task)
    return task
