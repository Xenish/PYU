import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.imports import ImportSession, ImportedAsset
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan, Task
from app.models.project import (
    ArchitectureComponent,
    Feature,
    Project,
    ProjectObjective,
    TechStackOption,
)
from app.models.quality import DoDItem, NFRItem, RiskItem


@pytest.mark.asyncio
async def test_basic_model_persistence():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:  # type: AsyncSession
        project = Project(name="Model Test", description="desc")
        session.add(project)
        await session.flush()

        session.add(ProjectObjective(project_id=project.id, title="Obj", text="t"))
        session.add(TechStackOption(project_id=project.id, notes="ts"))
        session.add(Feature(project_id=project.id, name="F1"))
        session.add(ArchitectureComponent(project_id=project.id, name="Comp", layer="backend"))
        session.add(DoDItem(project_id=project.id, category="functional", description="DoD"))
        session.add(NFRItem(project_id=project.id, type="performance", description="NFR"))
        session.add(RiskItem(project_id=project.id, description="Risk", impact=1, likelihood=1))

        epic = Epic(project_id=project.id, name="Epic 1")
        session.add(epic)
        await session.flush()

        sprint_plan = SprintPlan(project_id=project.id, name="Plan 1")
        session.add(sprint_plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=sprint_plan.id, index=1, name="Sprint 1")
        session.add(sprint)
        await session.flush()

        sprint_epic = SprintEpic(sprint_id=sprint.id, epic_id=epic.id)
        session.add(sprint_epic)
        task = Task(sprint_id=sprint.id, epic_id=epic.id, title="Task 1")
        session.add(task)

        import_session = ImportSession(project_id=project.id, source_type="repo")
        session.add(import_session)
        await session.flush()
        session.add(
            ImportedAsset(import_session_id=import_session.id, path="file.py", processing_status="done")
        )

        await session.commit()

    async with SessionLocal() as session:
        projects = (await session.execute(Project.__table__.select())).all()
        assert len(projects) == 1
        epics = (await session.execute(Epic.__table__.select())).all()
        assert len(epics) == 1

    await engine.dispose()
