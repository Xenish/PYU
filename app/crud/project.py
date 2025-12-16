from typing import Sequence

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.filters import only_active

from app.core.enums import ProjectStatus
from app.models.project import Project, ProjectStep
from app.repositories import project_repo
from app.schemas.project import ProjectCreate, ProjectStepCreate, ProjectUpdate


async def create_project(db: AsyncSession, payload: ProjectCreate) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        planning_detail_level=payload.planning_detail_level,
        language=payload.language,
        status=ProjectStatus.DRAFT,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def list_projects(db: AsyncSession) -> Sequence[Project]:
    return await project_repo.list_projects(db)


async def create_project_step(
    db: AsyncSession, project_id: int, payload: ProjectStepCreate
) -> ProjectStep:
    step = ProjectStep(
        project_id=project_id,
        step_type=payload.step_type,
        status=payload.status,
        last_input_hash=payload.last_input_hash,
        last_output_json=payload.last_output_json,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


async def list_project_steps(db: AsyncSession, project_id: int) -> Sequence[ProjectStep]:
    stmt = only_active(select(ProjectStep), ProjectStep).where(ProjectStep.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_project(db: AsyncSession, project_id: int, payload: ProjectUpdate) -> Project | None:
    project = await project_repo.get_project_by_id(db, project_id)
    if not project:
        return None
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.planning_detail_level is not None:
        project.planning_detail_level = payload.planning_detail_level
    if payload.language is not None:
        project.language = payload.language
    await db.flush()
    await db.refresh(project)
    return project


async def soft_delete_project(db: AsyncSession, project_id: int) -> Project | None:
    project = await project_repo.get_project_by_id(db, project_id)
    if not project:
        return None
    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return project
