from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.filters import only_active
from app.models.project import Project


async def list_projects(db: AsyncSession, include_deleted: bool = False) -> Sequence[Project]:
    stmt = select(Project)
    if not include_deleted:
        stmt = only_active(stmt, Project)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_project_by_id(db: AsyncSession, project_id: int, include_deleted: bool = False) -> Project | None:
    stmt = select(Project).where(Project.id == project_id)
    if not include_deleted:
        stmt = only_active(stmt, Project)
    result = await db.execute(stmt)
    return result.scalars().first()
