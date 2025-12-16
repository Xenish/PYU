import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import JobStatus
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.planning import Sprint, SprintPlan
from app.models.project import Project
from app.services import job_worker, job_engine


@pytest.fixture
def cancel_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init_models())
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client, SessionLocal
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.mark.asyncio
async def test_cancel_queued_job(cancel_client):
    client, SessionLocal = cancel_client

    async def seed():
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
            return project.id, sprint.id

    project_id, sprint_id = await seed()
    create_resp = client.post(
        "/jobs/task-pipeline-for-sprint",
        json={"project_id": project_id, "sprint_id": sprint_id},
    )
    job_id = create_resp.json()["id"]
    cancel_resp = client.post(f"/jobs/{job_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == JobStatus.CANCELLED.value

    # worker should skip cancelled
    async with SessionLocal() as session:
        job = await job_worker.process_next_job(session)
        assert job is None


@pytest.mark.asyncio
async def test_cancel_running_job_sets_flag(cancel_client, monkeypatch):
    client, SessionLocal = cancel_client

    async def seed():
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
            return project, sprint

    project, sprint = await seed()
    async with SessionLocal() as session:
        job = await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict=None)

    # set cancellation during progress update
    original_update = job_engine._update_progress  # type: ignore[attr-defined]

    async def fake_update(db, job_obj, pct, step):
        if step == "pass1":
            job_obj.cancellation_requested = True
        await original_update(db, job_obj, pct, step)

    monkeypatch.setattr(job_engine, "_update_progress", fake_update)  # type: ignore[attr-defined]

    # run worker should cancel mid-run
    async with SessionLocal() as session:
        job = await job_worker.process_next_job(session)
        assert job is not None
        assert job.status == JobStatus.CANCELLED.value
