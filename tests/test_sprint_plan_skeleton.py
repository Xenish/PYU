import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.planning import Epic
from app.models.project import Project
from app.services.sprint_planning import create_sprint_plan_skeleton


@pytest.mark.asyncio
async def test_sprint_plan_round_robin(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Proj", description="D")
        session.add(project)
        await session.flush()
        # Precreate epics
        epics = [Epic(project_id=project.id, name=f"E{i}") for i in range(1, 5)]
        session.add_all(epics)
        await session.commit()
        await session.refresh(project)

        plan = await create_sprint_plan_skeleton(session, project, num_sprints=2)
        assert plan.id is not None

        sprints = (
            await session.execute(
                plan.__table__.metadata.tables["sprints"].select().where(
                    plan.__table__.metadata.tables["sprints"].c.sprint_plan_id == plan.id
                )
            )
        ).fetchall()
        sprint_epics = (
            await session.execute(
                plan.__table__.metadata.tables["sprint_epics"].select()
            )
        ).fetchall()
        assert len(sprints) == 2
        assert len(sprint_epics) == 4

    await engine.dispose()
