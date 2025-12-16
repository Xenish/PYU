import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.planning import Epic, Sprint
from app.models.project import Project


@pytest.fixture
def update_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio

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


def test_patch_epic_and_sprint(update_client):
    client, SessionLocal = update_client
    # seed project, epic, sprint
    async def seed():
        async with SessionLocal() as session:
            project = Project(name="P", description="D")
            session.add(project)
            await session.flush()
            epic = Epic(project_id=project.id, name="E1")
            session.add(epic)
            sprint = Sprint(sprint_plan_id=1, index=1, name="S1")
            session.add(sprint)
            await session.commit()
            return epic.id, sprint.id

    import asyncio

    epic_id, sprint_id = asyncio.get_event_loop().run_until_complete(seed())

    resp_epic = client.patch(f"/epics/{epic_id}", json={"story_points": 8})
    assert resp_epic.status_code == 200
    assert resp_epic.json()["story_points"] == 8

    resp_sprint = client.patch(f"/sprints/{sprint_id}", json={"capacity_sp": 10})
    assert resp_sprint.status_code == 200
    assert resp_sprint.json()["capacity_sp"] == 10

    # 404 cases
    resp_missing = client.patch("/epics/9999", json={"story_points": 5})
    assert resp_missing.status_code == 404
    resp_missing_sprint = client.patch("/sprints/9999", json={"capacity_sp": 5})
    assert resp_missing_sprint.status_code == 404
