import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan, Task
from app.models.project import Project
from app.models.quality import DoDItem
from app.core.enums import TaskStatus


@pytest.fixture
def planning_client():
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
async def test_planning_overview(planning_client):
    client, SessionLocal = planning_client

    async with SessionLocal() as session:
        project = Project(name="P", description="D")
        session.add(project)
        await session.flush()
        plan = SprintPlan(project_id=project.id, name="Plan")
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned", capacity_sp=10)
        session.add(sprint)
        epic = Epic(project_id=project.id, name="E1", description="d", story_points=5, category="feature")
        session.add(epic)
        await session.flush()
        session.add(SprintEpic(sprint_id=sprint.id, epic_id=epic.id))
        session.add(DoDItem(project_id=project.id, description="ship", category="release"))
        await session.commit()
        project_id = project.id

    resp = client.get(f"/projects/{project_id}/planning/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["epics"][0]["sprint_ids"] == [sprint.id]
    assert data["sprints"][0]["allocated_sp"] == 5
    assert data["sprints"][0]["quality_summary"]["dod_count"] == 1


@pytest.mark.asyncio
async def test_task_status_update_and_board_view(planning_client):
    client, SessionLocal = planning_client
    async with SessionLocal() as session:
        project = Project(name="P2", description="D2")
        session.add(project)
        await session.flush()
        plan = SprintPlan(project_id=project.id, name="Plan2")
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
        session.add(sprint)
        epic = Epic(project_id=project.id, name="EpicX", description="d")
        session.add(epic)
        await session.flush()
        task = Task(
            project_id=project.id,
            sprint_id=sprint.id,
            epic_id=epic.id,
            title="T1",
            description="d",
            status=TaskStatus.TODO,
        )
        session.add(task)
        await session.commit()
        task_id = task.id
        sprint_id = sprint.id

    # valid transition
    resp = client.patch(f"/tasks/{task_id}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # invalid transition
    bad = client.patch(f"/tasks/{task_id}/status", json={"status": "todo"})
    assert bad.status_code == 400

    # board view includes epic_name
    board = client.get(f"/sprints/{sprint_id}/tasks?for_board=true")
    assert board.status_code == 200
    assert board.json()[0]["epic_name"] == "EpicX"
