import asyncio
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.api.routes import planning as planning_router
from app.api.routes import tasks as tasks_router
from app.api.routes import jobs as jobs_router
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.job import Job
from app.models.planning import Epic, EpicDependency, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.schemas.jobs import JobCreateTaskPipeline
from app.core.enums import JobStatus


@pytest.fixture
def api_client(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init_models())
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    # patch planning services to avoid heavy logic
    async def fake_generate_epics_for_project(db, project):
        epic = Epic(project_id=project.id, name="E1", description="desc")
        db.add(epic)
        await db.flush()
        return [epic]

    async def fake_generate_epic_dependencies_for_project(db, project_id):
        result = await db.execute(Epic.__table__.select().where(Epic.project_id == project_id))
        row = result.first()
        if not row:
            return []
        dep = EpicDependency(epic_id=row.id, depends_on_epic_id=row.id)
        return [dep]

    async def fake_estimate_story_points_for_epics(db, project_id):
        result = await db.execute(Epic.__table__.select().where(Epic.project_id == project_id))
        epics = []
        for row in result.fetchall():
            epics.append(Epic(id=row.id, project_id=project_id, name=row.name, description=row.description, story_points=3))
        return epics

    async def fake_create_capacity_aware_sprint_plan(db, project, num_sprints=3, default_capacity_sp=None):
        plan = SprintPlan(project_id=project.id, name="Plan")
        db.add(plan)
        await db.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
        db.add(sprint)
        epic = Epic(project_id=project.id, name="E1", description="desc")
        db.add(epic)
        await db.flush()
        se = SprintEpic(sprint_id=sprint.id, epic_id=epic.id)
        return plan, [se], [], {}

    async def fake_create_sprint_plan_skeleton(db, project, num_sprints=3):
        plan = SprintPlan(project_id=project.id, name="Plan")
        db.add(plan)
        await db.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
        db.add(sprint)
        await db.flush()
        return plan

    monkeypatch.setattr(planning_router, "generate_epics_for_project", fake_generate_epics_for_project)
    monkeypatch.setattr(planning_router, "generate_epic_dependencies_for_project", fake_generate_epic_dependencies_for_project)
    monkeypatch.setattr(planning_router, "estimate_story_points_for_epics", fake_estimate_story_points_for_epics)
    monkeypatch.setattr(planning_router, "create_capacity_aware_sprint_plan", fake_create_capacity_aware_sprint_plan)
    monkeypatch.setattr(planning_router, "create_sprint_plan_skeleton", fake_create_sprint_plan_skeleton)

    # patch task services
    async def fake_generate_draft_tasks_for_sprint(db, sprint):
        return []

    async def fake_refine_tasks_pass2_for_sprint(db, sprint):
        return []

    async def fake_refine_tasks_pass3_for_sprint(db, sprint_id):
        return []

    monkeypatch.setattr(tasks_router, "generate_draft_tasks_for_sprint", fake_generate_draft_tasks_for_sprint)
    monkeypatch.setattr(tasks_router, "refine_tasks_pass2_for_sprint", fake_refine_tasks_pass2_for_sprint)
    monkeypatch.setattr(tasks_router, "refine_tasks_pass3_for_sprint", fake_refine_tasks_pass3_for_sprint)

    # patch job services
    async def fake_create_job_for_task_pipeline(db, project, sprint, payload_dict=None):
        job = Job(
            project_id=project.id,
            sprint_id=sprint.id,
            type="TASK_PIPELINE_FOR_SPRINT",
            status=JobStatus.QUEUED.value,
            payload_json="{}",
            created_at=datetime.utcnow(),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def fake_process_next_job(db):
        result = await db.execute(Job.__table__.select())
        row = result.first()
        if not row:
            return None
        job = await db.get(Job, row.id)
        job.status = JobStatus.COMPLETED.value
        await db.commit()
        await db.refresh(job)
        return job

    monkeypatch.setattr(jobs_router, "create_job_for_task_pipeline", fake_create_job_for_task_pipeline)
    monkeypatch.setattr(jobs_router, "process_next_job", fake_process_next_job)

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client, SessionLocal
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.mark.asyncio
async def test_health_and_projects_endpoints(api_client):
    client, SessionLocal = api_client
    assert client.get("/health").status_code == 200
    assert client.get("/health/ping").status_code == 200

    # create project
    response = client.post("/projects", json={"name": "Proj", "description": "Desc"})
    assert response.status_code == 201
    project_id = response.json()["id"]

    # list projects
    list_resp = client.get("/projects")
    assert any(p["id"] == project_id for p in list_resp.json())

    # create sprint plan/sprint for later tests
    async with SessionLocal() as session:
        plan = SprintPlan(project_id=project_id, name="Plan", created_at=datetime.utcnow())
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
        session.add(sprint)
        await session.commit()
        sprint_id = sprint.id

    # list project sprints
    sprint_resp = client.get(f"/projects/{project_id}/sprints")
    assert sprint_resp.status_code == 200
    assert sprint_resp.json()[0]["id"] == sprint_id


@pytest.mark.asyncio
async def test_planning_and_tasks_and_jobs(api_client):
    client, SessionLocal = api_client

    # seed project and sprint
    async with SessionLocal() as session:
        project = Project(name="P", description="D")
        session.add(project)
        await session.flush()
        plan = SprintPlan(project_id=project.id, name="Plan")
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
        session.add(sprint)
        await session.commit()
        project_id = project.id
        sprint_id = sprint.id

    # planning endpoints
    assert client.post(f"/projects/{project_id}/planning/generate-epics").status_code == 200
    assert client.post(f"/projects/{project_id}/planning/estimate-epic-story-points").status_code == 200
    assert client.post(f"/projects/{project_id}/planning/generate-capacity-plan").status_code == 200
    assert client.post(f"/projects/{project_id}/planning/generate-sprint-plan").status_code == 200

    # tasks endpoints
    assert client.get(f"/sprints/{sprint_id}/tasks").status_code == 200
    assert (
        client.post(f"/sprints/{sprint_id}/tasks/generate-draft").status_code == 200
    )
    assert client.post(f"/sprints/{sprint_id}/tasks/refine-pass2").status_code == 200
    assert client.post(f"/sprints/{sprint_id}/tasks/refine-pass3").status_code == 200

    # job endpoints
    payload = JobCreateTaskPipeline(project_id=project_id, sprint_id=sprint_id)
    job_resp = client.post("/jobs/task-pipeline-for-sprint", json=payload.model_dump())
    assert job_resp.status_code == 200
    job_id = job_resp.json()["id"]
    assert client.get(f"/jobs/{job_id}").status_code == 200
    assert client.get(f"/projects/{project_id}/jobs").status_code == 200
    assert client.post(f"/jobs/{job_id}/cancel").status_code in (200, 409)
    # run-next uses patched worker
    assert client.post("/jobs/run-next").status_code == 200


@pytest.mark.asyncio
async def test_planning_update_patch(api_client):
    client, SessionLocal = api_client
    async with SessionLocal() as session:
        project = Project(name="P2", description="D2")
        session.add(project)
        await session.flush()
        epic = Epic(project_id=project.id, name="E", description="d")
        session.add(epic)
        plan = SprintPlan(project_id=project.id, name="Plan2")
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
        session.add(sprint)
        await session.commit()
        epic_id = epic.id
        sprint_id = sprint.id

    ep_resp = client.patch(f"/epics/{epic_id}", json={"story_points": 5})
    assert ep_resp.status_code == 200
    sp_resp = client.patch(f"/sprints/{sprint_id}", json={"capacity_sp": 10})
    assert sp_resp.status_code == 200
