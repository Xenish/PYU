import asyncio
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.project import (
    ArchitectureComponent,
    Feature,
    Project,
    ProjectObjective,
    ProjectStep,
    TechStackOption,
)
from app.models.quality import DoDItem, NFRItem, RiskItem
from app.schemas.llm.architecture import ArchitectureLLMResponse
from app.schemas.llm.features import FeatureLLMResponse
from app.schemas.llm.objective import ObjectiveLLMResponse
from app.schemas.llm.quality import QualityLLMResponse
from app.schemas.llm.tech_stack import TechStackLLMResponse
from app.services import objective_step, quality_steps, spec_steps


@pytest.fixture
def item_flow_client(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init_models())
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    async def fake_call_llm(prompt, response_model, **kwargs):
        if response_model is ObjectiveLLMResponse:
            return ObjectiveLLMResponse.model_validate(
                {"objectives": [{"title": "Obj", "description": "Desc", "priority": 1}]}
            )
        if response_model is TechStackLLMResponse:
            return TechStackLLMResponse.model_validate(
                {
                    "items": [
                        {"category": "frontend", "name": "Next.js", "rationale": "r"},
                        {"category": "backend", "name": "FastAPI", "rationale": "r"},
                    ]
                }
            )
        if response_model is FeatureLLMResponse:
            return FeatureLLMResponse.model_validate(
                {
                    "features": [
                        {"title": "F1", "description": "d1", "importance": 1, "feature_type": "must"},
                        {"title": "F2", "description": "d2", "importance": 1, "feature_type": "must"},
                    ]
                }
            )
        if response_model is ArchitectureLLMResponse:
            return ArchitectureLLMResponse.model_validate(
                {
                    "components": [
                        {"name": "API", "layer": "backend", "description": "d", "responsibilities": ["r"]},
                        {"name": "UI", "layer": "frontend", "description": "d", "responsibilities": ["r"]},
                    ]
                }
            )
        if response_model is QualityLLMResponse:
            return QualityLLMResponse.model_validate(
                {
                    "dod_items": [
                        {"description": "DoD1", "category": "functional", "test_method": "t", "done_when": "dw", "priority": 1}
                    ],
                    "nfr_items": [{"type": "performance", "description": "fast", "measurable_target": "p95"}],
                    "risks": [{"description": "Risk1", "impact": 1, "likelihood": 1, "mitigation": "m"}],
                }
            )
        raise ValueError("Unexpected response model")

    monkeypatch.setattr(objective_step, "call_llm", fake_call_llm)
    monkeypatch.setattr(spec_steps, "call_llm", fake_call_llm)
    monkeypatch.setattr(quality_steps, "call_llm", fake_call_llm)

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client, SessionLocal
    asyncio.get_event_loop().run_until_complete(engine.dispose())


async def _create_project(session):
    project = Project(name="Proj", description="Desc")
    session.add(project)
    await session.flush()
    await session.commit()
    await session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_full_item_selection_approval_flow(item_flow_client):
    client, SessionLocal = item_flow_client
    async with SessionLocal() as session:
        project = await _create_project(session)

    # Generate features via endpoint (creates pending/complete step)
    assert client.post(f"/projects/{project.id}/steps/features/run").status_code == 200

    # select all then approve
    sel_resp = client.post(f"/projects/{project.id}/items/feature/select-all")
    assert sel_resp.status_code == 200
    assert sel_resp.json()["selected_count"] >= 1

    approve_resp = client.post(f"/projects/{project.id}/steps/{StepType.FEATURES.value}/approve")
    assert approve_resp.status_code == 200

    async with SessionLocal() as session:
        step = (
            await session.execute(
                select(ProjectStep).where(
                    ProjectStep.project_id == project.id,
                    ProjectStep.step_type == StepType.FEATURES,
                )
            )
        ).scalars().first()
        assert step.approval_status == ApprovalStatus.APPROVED


@pytest.mark.asyncio
async def test_multi_step_selection_flow_all_items(item_flow_client):
    client, SessionLocal = item_flow_client
    async with SessionLocal() as session:
        project = await _create_project(session)

    # run all steps to create items
    assert client.post(f"/projects/{project.id}/steps/objective/run").status_code == 200
    assert client.post(f"/projects/{project.id}/steps/tech-stack/run").status_code == 200
    assert client.post(f"/projects/{project.id}/steps/features/run").status_code == 200
    assert client.post(f"/projects/{project.id}/steps/architecture/run").status_code == 200
    assert client.post(f"/projects/{project.id}/steps/quality/run").status_code == 200

    # select all item types
    for item_type in ["objective", "tech_stack", "feature", "architecture", "dod", "nfr", "risk"]:
        resp = client.post(f"/projects/{project.id}/items/{item_type}/select-all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == data["selected_count"]

    # verify selection summary reflects selection
    for item_type in ["objective", "tech_stack", "feature", "architecture", "dod", "nfr", "risk"]:
        summary = client.get(f"/projects/{project.id}/items/{item_type}/selection-summary")
        assert summary.status_code == 200
        data = summary.json()
        assert data["total_count"] == data["selected_count"]


@pytest.mark.asyncio
async def test_reject_and_regenerate_preserves_selected(item_flow_client):
    client, SessionLocal = item_flow_client
    async with SessionLocal() as session:
        project = await _create_project(session)

    # initial generation
    assert client.post(f"/projects/{project.id}/steps/features/run").status_code == 200

    detail = client.get(f"/projects/{project.id}/spec-wizard/detail").json()
    first_feature_id = detail["features"][0]["id"]

    # select first, leave second unselected
    assert (
        client.post(
            f"/items/feature/{first_feature_id}/toggle-select",
            json={"project_id": project.id},
        ).status_code
        == 200
    )

    # reject step
    reject_resp = client.post(
        f"/projects/{project.id}/steps/{StepType.FEATURES.value}/reject",
        json={"feedback": "needs changes"},
    )
    assert reject_resp.status_code == 200

    # regenerate
    regen_resp = client.post(f"/projects/{project.id}/steps/{StepType.FEATURES.value}/regenerate")
    assert regen_resp.status_code == 200

    async with SessionLocal() as session:
        # selected remains and not deleted
        selected = await session.get(Feature, first_feature_id)
        assert selected.is_selected is True
        assert selected.is_deleted is False

        # previously unselected should be soft-deleted
        others = (
            await session.execute(
                select(Feature).where(
                    Feature.project_id == project.id,
                    Feature.id != first_feature_id,
                )
            )
        ).scalars().all()
        assert any(f.is_deleted for f in others)

        # new features are created unselected
        new_unselected = [f for f in others if not f.is_deleted]
        assert all(f.is_selected is False for f in new_unselected)
