from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import Epic
from app.models.project import Feature


def _heuristic_story_points(feature_count: int, category: str | None) -> int:
    base = 3
    if feature_count <= 2:
        base = 3
    elif feature_count <= 5:
        base = 5
    elif feature_count <= 8:
        base = 8
    else:
        base = 13
    if category and category.lower() == "platform":
        base += 2
    return min(base, 20)


async def estimate_story_points_for_epics(db: AsyncSession, project_id: int):
    epics = (await db.execute(select(Epic).where(Epic.project_id == project_id))).scalars().all()
    feature_map = (
        await db.execute(select(Feature).where(Feature.project_id == project_id))
    ).scalars().all()
    feat_count = len(feature_map)
    for epic in epics:
        epic.story_points = _heuristic_story_points(feat_count, epic.category)
    await db.commit()
    return epics
