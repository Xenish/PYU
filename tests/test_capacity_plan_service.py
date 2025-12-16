import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.project import Project
from app.services.sprint_planning import create_capacity_aware_sprint_plan


@pytest.mark.asyncio
async def test_capacity_plan_generates_epics(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Pcap", description="D")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        plan, assignments, backlog, quality = await create_capacity_aware_sprint_plan(
            session, project, num_sprints=1, default_capacity_sp=0
        )
        assert plan.id is not None
        assert backlog is not None
        assert isinstance(quality, dict)

    await engine.dispose()
