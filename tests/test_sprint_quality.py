import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.models.quality import DoDItem, NFRItem
from app.services.sprint_quality import build_sprint_quality_summaries


@pytest.mark.asyncio
async def test_sprint_quality_summary():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="PQ", description="D")
        session.add(project)
        await session.flush()
        ep = Epic(project_id=project.id, name="E1")
        plan = SprintPlan(project_id=project.id, name="PlanQ")
        session.add_all([ep, plan])
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1")
        session.add(sprint)
        await session.flush()
        se = SprintEpic(sprint_id=sprint.id, epic_id=ep.id)
        session.add(se)
        session.add(DoDItem(project_id=project.id, category="functional", description="DoD"))
        session.add(NFRItem(project_id=project.id, type="performance", description="NFR"))
        await session.commit()

        summary = await build_sprint_quality_summaries(session, plan)
        assert sprint.id in summary
        assert summary[sprint.id]["dod_count"] == 1
        assert "performance" in summary[sprint.id]["nfr_categories"]

    await engine.dispose()
