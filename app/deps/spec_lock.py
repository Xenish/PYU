"""Spec lock guard dependency for FastAPI endpoints."""
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.project_repo import get_project_by_id


async def ensure_project_unlocked(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Dependency to ensure a project's spec is not locked.

    Raises 403 if project.spec_locked is True.
    Use this dependency on wizard and planning endpoints to prevent
    modifications after sprint plan approval.
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.spec_locked:
        raise HTTPException(
            status_code=403,
            detail="Project spec is locked. Please clone the project to make changes.",
        )
