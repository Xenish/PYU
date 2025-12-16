import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.project import Project


@pytest.fixture
def task_client():
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
async def test_task_generation_endpoint(task_client, monkeypatch):
    client, SessionLocal = task_client

    async def fake_llm(prompt, response_model, **kwargs):
        return response_model.model_validate(
            {"tasks": [{"title": "Task1", "description": "Desc"}]}
        )

    from app.services import task_generation

    monkeypatch.setattr(task_generation, "call_llm", fake_llm)

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
            return sprint.id

    sprint_id = await seed()

    resp = client.post(f"/sprints/{sprint_id}/tasks/generate-draft")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
