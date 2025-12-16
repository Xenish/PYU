import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.api.routes import jobs as jobs_routes
from app.schemas.jobs import JobCreateTaskPipeline
from app.models.project import Project
from app.models.planning import Sprint, SprintPlan


@pytest.mark.asyncio
async def test_create_task_pipeline_job_route_unit():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="P", description="D")
        session.add(project)
        await session.flush()
        plan = SprintPlan(project_id=project.id, name="Plan")
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1")
        session.add(sprint)
        await session.commit()

        payload = JobCreateTaskPipeline(project_id=project.id, sprint_id=sprint.id)
        job = await jobs_routes.create_task_pipeline_job(payload, db=session)
        assert job.status == "queued"

    await engine.dispose()
