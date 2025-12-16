import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.core.enums import TaskStatus
from app.services import job_engine, task_generation, task_refinement, task_split


@pytest.fixture
def jobs_client():
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
async def test_job_api_runs_pipeline(jobs_client, monkeypatch):
    client, SessionLocal = jobs_client

    async def fake_pass1(db, sprint, job_id=None):
        return [object()]

    async def fake_pass2(db, sprint, job_id=None):
        return [object(), object()]

    class Dummy:
        def __init__(self):
            self.status = TaskStatus.READY_FOR_DEV

    async def fake_pass3(db, sprint_id, job_id=None):
        return [Dummy()]

    # Patch on job_engine namespace so runner uses stubs
    monkeypatch.setattr(task_generation, "generate_draft_tasks_for_sprint", fake_pass1)
    monkeypatch.setattr(task_refinement, "refine_tasks_pass2_for_sprint", fake_pass2)
    monkeypatch.setattr(task_split, "refine_tasks_pass3_for_sprint", fake_pass3)
    monkeypatch.setattr(job_engine, "generate_draft_tasks_for_sprint", fake_pass1)
    monkeypatch.setattr(job_engine, "refine_tasks_pass2_for_sprint", fake_pass2)
    monkeypatch.setattr(job_engine, "refine_tasks_pass3_for_sprint", fake_pass3)

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
            await session.flush()
            epic = Epic(project_id=project.id, name="E1")
            session.add(epic)
            await session.flush()
            session.add(SprintEpic(sprint_id=sprint.id, epic_id=epic.id))
            await session.commit()
            return project.id, sprint.id

    project_id, sprint_id = await seed()

    resp = client.post(
        "/jobs/task-pipeline-for-sprint",
        json={"project_id": project_id, "sprint_id": sprint_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    job_id = data["id"]

    # run worker once
    resp_run = client.post("/jobs/run-next")
    assert resp_run.status_code == 200
    data_run = resp_run.json()
    assert data_run["status"] == "completed"
    summary = json.loads(data_run["result_json"])
    assert summary["ready_for_dev_tasks"] == 1

    resp_get = client.get(f"/jobs/{job_id}")
    assert resp_get.status_code == 200
    resp_list = client.get(f"/projects/{project_id}/jobs")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1


def test_run_next_job_without_queue_returns_none(jobs_client):
    client, _ = jobs_client
    resp = client.post("/jobs/run-next")
    assert resp.status_code == 200
    assert resp.json() is None


def test_get_job_not_found(jobs_client):
    client, _ = jobs_client
    resp = client.get("/jobs/9999")
    assert resp.status_code == 404


def test_create_job_with_invalid_project_returns_404(jobs_client):
    client, _ = jobs_client
    resp = client.post(
        "/jobs/task-pipeline-for-sprint",
        json={"project_id": 999, "sprint_id": 1},
    )
    assert resp.status_code == 404


def test_create_job_with_invalid_sprint_returns_404(jobs_client):
    client, _ = jobs_client
    resp = client.post(
        "/jobs/task-pipeline-for-sprint",
        json={"project_id": 1, "sprint_id": 999},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_completed_job_returns_conflict(jobs_client, monkeypatch):
    client, SessionLocal = jobs_client

    async def fake_pass1(db, sprint):
        return []

    async def fake_pass2(db, sprint):
        return []

    async def fake_pass3(db, sprint_id):
        return []

    monkeypatch.setattr(job_engine, "generate_draft_tasks_for_sprint", fake_pass1)
    monkeypatch.setattr(job_engine, "refine_tasks_pass2_for_sprint", fake_pass2)
    monkeypatch.setattr(job_engine, "refine_tasks_pass3_for_sprint", fake_pass3)

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
    client.post("/jobs/run-next")
    cancel_resp = client.post(f"/jobs/{job_id}/cancel")
    assert cancel_resp.status_code == 409
