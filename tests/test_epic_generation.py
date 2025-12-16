import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.project import Project, Feature, ArchitectureComponent
from app.services.epic_generation import generate_epics_for_project


@pytest.mark.asyncio
async def test_generate_epics_clear_and_regenerate():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Proj", description="D")
        session.add(project)
        await session.flush()
        session.add(Feature(project_id=project.id, name="Login"))
        session.add(ArchitectureComponent(project_id=project.id, name="API Gateway", layer="infra"))
        await session.commit()
        await session.refresh(project)

        epics = await generate_epics_for_project(session, project)
        assert len(epics) == 2
        # regenerate clears previous
        epics2 = await generate_epics_for_project(session, project)
        assert len(epics2) == 2

    await engine.dispose()
