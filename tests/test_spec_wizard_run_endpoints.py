import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.project import Project
from app.api.routes import spec_wizard as wizard_module


@pytest.fixture
def run_client(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init_models())
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    # monkeypatch step runners to avoid LLM
    async def fake_obj(db, pid):
        return []

    async def fake_ts(db, pid):
        return []

    async def fake_feat(db, pid):
        return []

    async def fake_arch(db, pid):
        return []

    async def fake_quality(db, pid):
        return [], [], []

    monkeypatch.setattr(wizard_module, "run_objective_step", fake_obj)
    monkeypatch.setattr(wizard_module, "run_tech_stack_step", fake_ts)
    monkeypatch.setattr(wizard_module, "run_feature_step", fake_feat)
    monkeypatch.setattr(wizard_module, "run_architecture_step", fake_arch)
    monkeypatch.setattr(wizard_module, "run_quality_steps", fake_quality)

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client, SessionLocal
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.mark.asyncio
async def test_run_endpoints(run_client):
    client, SessionLocal = run_client

    async def seed():
        async with SessionLocal() as session:
            project = Project(name="P", description="D")
            session.add(project)
            await session.commit()
            return project.id

    pid = await seed()

    assert client.post(f"/projects/{pid}/steps/objective/run").status_code == 200
    assert client.post(f"/projects/{pid}/steps/tech-stack/run").status_code == 200
    assert client.post(f"/projects/{pid}/steps/features/run").status_code == 200
    assert client.post(f"/projects/{pid}/steps/architecture/run").status_code == 200
    assert client.post(f"/projects/{pid}/steps/quality/run").status_code == 200
