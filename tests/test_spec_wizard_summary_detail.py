import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.project import Project, ProjectObjective, ArchitectureComponent, TechStackOption
from app.models.quality import DoDItem
from app.models.project import Feature
from app.models.quality import NFRItem, RiskItem


@pytest.fixture
def wizard_client():
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
async def test_spec_wizard_summary_and_detail(wizard_client):
    client, SessionLocal = wizard_client

    async def seed():
        async with SessionLocal() as session:
            project = Project(name="P", description="D")
            session.add(project)
            await session.flush()
            session.add(ProjectObjective(project_id=project.id, title="Obj1", text="desc"))
            session.add(Feature(project_id=project.id, name="Feat1", description="desc"))
            session.add(
                ArchitectureComponent(project_id=project.id, name="Comp1", layer="service")
            )
            session.add(DoDItem(project_id=project.id, description="dod", category="release"))
            session.add(NFRItem(project_id=project.id, type="performance", description="fast"))
            session.add(RiskItem(project_id=project.id, description="risk", impact=1, likelihood=1))
            session.add(
                TechStackOption(
                    project_id=project.id,
                    frontend={"name": "Next.js"},
                    backend={"name": "FastAPI"},
                )
            )
            await session.commit()
            return project.id

    project_id = await seed()

    resp = client.get(f"/projects/{project_id}/spec-wizard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["steps"]) == 5

    resp_detail = client.get(f"/projects/{project_id}/spec-wizard/detail")
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["objectives"]
