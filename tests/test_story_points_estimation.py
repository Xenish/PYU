import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.planning import Epic
from app.models.project import Project
from app.services.story_points import estimate_story_points_for_epics


@pytest.mark.asyncio
async def test_story_point_estimation():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="ProjSP", description="D")
        session.add(project)
        await session.flush()
        epics = [Epic(project_id=project.id, name="E1", category="feature") for _ in range(3)]
        session.add_all(epics)
        await session.commit()

        updated = await estimate_story_points_for_epics(session, project.id)
        assert all(e.story_points is not None and e.story_points > 0 for e in updated)

    await engine.dispose()


@pytest.mark.asyncio
async def test_story_point_estimation_platform_category():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="ProjPlat", description="D")
        session.add(project)
        await session.flush()
        session.add(Epic(project_id=project.id, name="Infra", category="platform"))
        await session.commit()

        updated = await estimate_story_points_for_epics(session, project.id)
        assert updated[0].story_points is not None and updated[0].story_points >= 3

    await engine.dispose()
