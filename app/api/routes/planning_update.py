from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.planning import Epic, Sprint
from app.schemas.planning import EpicRead, SprintRead

router = APIRouter()


@router.patch("/epics/{epic_id}", response_model=EpicRead)
async def update_epic(epic_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    epic = await db.get(Epic, epic_id)
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    if "story_points" in payload:
        epic.story_points = payload["story_points"]
    await db.commit()
    await db.refresh(epic)
    return epic


@router.patch("/sprints/{sprint_id}", response_model=SprintRead)
async def update_sprint(sprint_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    sprint = await db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    if "capacity_sp" in payload:
        sprint.capacity_sp = payload["capacity_sp"]
    await db.commit()
    await db.refresh(sprint)
    return sprint
