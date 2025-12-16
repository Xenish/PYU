import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import StepStatus, StepType
from app.db.base import Base
from app.models.project import ProjectStep, Project
from app.services import objective_step, spec_steps, quality_steps
from app.main import create_app
from fastapi.testclient import TestClient
from app.db.session import get_db
from sqlalchemy import select


@pytest.fixture
def api_client():
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
async def test_wizard_end_to_end(monkeypatch, api_client):
    client, SessionLocal = api_client
    # Patch all call_llm to deterministic outputs
    async def fake_obj(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"objectives": [{"title": "O1", "description": "d", "priority": 1}]}
        )

    async def fake_ts(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate({"items": [{"category": "backend", "name": "FastAPI"}]})

    async def fake_feat(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"features": [{"title": "F1", "description": "d", "importance": 3, "feature_type": "must"}]}
        )

    async def fake_arch(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"components": [{"name": "API", "layer": "backend", "responsibilities": ["r"]}]}
        )

    async def fake_quality(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {
                "dod_items": [{"description": "DoD", "category": "functional", "priority": 1}],
                "nfr_items": [{"type": "performance", "description": "fast"}],
                "risks": [{"description": "Risk", "impact": 1, "likelihood": 1}],
            }
        )

    monkeypatch.setattr(objective_step, "call_llm", fake_obj)
    monkeypatch.setattr(spec_steps, "call_llm", fake_ts)
    monkeypatch.setattr(quality_steps, "call_llm", fake_quality)

    # create project
    resp = client.post("/projects", json={"name": "Proj", "description": "D", "planning_detail_level": "low"})
    project_id = resp.json()["id"]

    client.post(f"/projects/{project_id}/steps/objective/run")
    client.post(f"/projects/{project_id}/steps/tech-stack/run")
    monkeypatch.setattr(spec_steps, "call_llm", fake_feat)
    client.post(f"/projects/{project_id}/steps/features/run")
    monkeypatch.setattr(spec_steps, "call_llm", fake_arch)
    client.post(f"/projects/{project_id}/steps/architecture/run")
    client.post(f"/projects/{project_id}/steps/quality/run")

    async with SessionLocal() as session:
        steps = (
            await session.execute(
                select(ProjectStep).where(ProjectStep.project_id == project_id)
            )
        ).scalars().all()
        assert len(steps) >= 5
        assert all(s.status == StepStatus.COMPLETED for s in steps)

    assert project_id > 0
