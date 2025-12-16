import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.project import Project, Feature, ArchitectureComponent


@pytest.fixture
def planning_client():
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


@pytest.mark.asyncio
async def test_planning_endpoints(planning_client):
    client, SessionLocal = planning_client

    resp = client.post("/projects", json={"name": "ProjP", "description": "Desc", "planning_detail_level": "low"})
    project_id = resp.json()["id"]

    # seed spec
    async with SessionLocal() as session:
        session.add(Feature(project_id=project_id, name="Login"))
        session.add(ArchitectureComponent(project_id=project_id, name="API", layer="backend"))
        await session.commit()

    resp_epic = client.post(f"/projects/{project_id}/planning/generate-epics")
    assert resp_epic.status_code == 200
    assert resp_epic.json()["epics"]

    resp_plan = client.post(f"/projects/{project_id}/planning/generate-sprint-plan", params={"num_sprints": 2})
    assert resp_plan.status_code == 200
    body = resp_plan.json()
    assert body["sprint_plan"]["id"]
    assert len(body["sprints"]) == 2
    assert body["sprint_epics"]

    resp_sp = client.post(f"/projects/{project_id}/planning/estimate-epic-story-points")
    assert resp_sp.status_code == 200

    resp_capacity = client.post(
        f"/projects/{project_id}/planning/generate-capacity-plan",
        params={"num_sprints": 2, "default_capacity_sp": 5},
    )
    assert resp_capacity.status_code == 200
    assert resp_capacity.json()["sprint_epics"] or resp_capacity.json()["unscheduled_epics"] == []
    assert "quality_summary" in resp_capacity.json()


@pytest.mark.asyncio
async def test_capacity_plan_without_existing_epics(planning_client):
    client, SessionLocal = planning_client
    resp = client.post("/projects", json={"name": "ProjEmpty", "description": "Desc", "planning_detail_level": "low"})
    project_id = resp.json()["id"]
    # no epics/features seeded
    resp_capacity = client.post(
        f"/projects/{project_id}/planning/generate-capacity-plan",
        params={"num_sprints": 1, "default_capacity_sp": 5},
    )
    assert resp_capacity.status_code == 200
    body = resp_capacity.json()
    assert body["sprints"]
    assert "quality_summary" in body
