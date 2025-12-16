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
from app.models.project import Feature, Project, ProjectObjective, ProjectStep
from app.models.quality import DoDItem
from app.services import spec_steps
from app.schemas.llm.features import FeatureLLMResponse


@pytest.fixture
def item_client():
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


async def _create_project(session):
    project = Project(name="Proj", description="Desc")
    session.add(project)
    await session.flush()
    await session.commit()
    await session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_toggle_item_selection_success(item_client):
    client, SessionLocal = item_client
    async with SessionLocal() as session:
        project = await _create_project(session)
        obj = ProjectObjective(project_id=project.id, title="O1", text="t1")
        session.add(obj)
        await session.commit()
        await session.refresh(obj)

    resp = client.post(
        f"/items/objective/{obj.id}/toggle-select", json={"project_id": project.id}
    )
    assert resp.status_code == 200
    assert resp.json()["is_selected"] is True

    async with SessionLocal() as session:
        refreshed = await session.get(ProjectObjective, obj.id)
        assert refreshed.is_selected is True


def test_toggle_item_selection_not_found(item_client):
    client, _ = item_client
    resp = client.post("/items/objective/999/toggle-select", json={"project_id": 1})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_select_all_items(item_client):
    client, SessionLocal = item_client
    async with SessionLocal() as session:
        project = await _create_project(session)
        feats = [
            Feature(project_id=project.id, name="f1", description="d1"),
            Feature(project_id=project.id, name="f2", description="d2"),
        ]
        session.add_all(feats)
        await session.commit()

    resp = client.post(f"/projects/{project.id}/items/feature/select-all")
    assert resp.status_code == 200
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Feature).where(Feature.project_id == project.id)
            )
        ).scalars().all()
        assert all(f.is_selected for f in rows)


@pytest.mark.asyncio
async def test_deselect_all_items(item_client):
    client, SessionLocal = item_client
    async with SessionLocal() as session:
        project = await _create_project(session)
        feats = [
            Feature(project_id=project.id, name="f1", description="d1", is_selected=True),
            Feature(project_id=project.id, name="f2", description="d2", is_selected=True),
        ]
        session.add_all(feats)
        await session.commit()

    resp = client.post(f"/projects/{project.id}/items/feature/deselect-all")
    assert resp.status_code == 200
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Feature).where(Feature.project_id == project.id)
            )
        ).scalars().all()
        assert all(not f.is_selected for f in rows)


@pytest.mark.asyncio
async def test_approve_step_without_selection_fails(item_client):
    client, SessionLocal = item_client
    async with SessionLocal() as session:
        project = await _create_project(session)
        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.FEATURES,
            status=StepStatus.COMPLETED,
            approval_status=ApprovalStatus.PENDING,
        )
        session.add(step)
        session.add(Feature(project_id=project.id, name="f1", description="d1"))
        await session.commit()

    resp = client.post(f"/projects/{project.id}/steps/{StepType.FEATURES.value}/approve")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_approve_step_with_selection_succeeds(item_client):
    client, SessionLocal = item_client
    async with SessionLocal() as session:
        project = await _create_project(session)
        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.FEATURES,
            status=StepStatus.COMPLETED,
            approval_status=ApprovalStatus.PENDING,
        )
        session.add(step)
        session.add(Feature(project_id=project.id, name="f1", description="d1", is_selected=True))
        await session.commit()

    resp = client.post(f"/projects/{project.id}/steps/{StepType.FEATURES.value}/approve")
    assert resp.status_code == 200
    async with SessionLocal() as session:
        refreshed = (
            await session.execute(
                select(ProjectStep).where(
                    ProjectStep.project_id == project.id,
                    ProjectStep.step_type == StepType.FEATURES,
                )
            )
        ).scalars().first()
        assert refreshed.approval_status == ApprovalStatus.APPROVED


@pytest.mark.asyncio
async def test_regenerate_preserves_selected_and_soft_deletes_unselected(monkeypatch, item_client):
    client, SessionLocal = item_client

    async def fake_call_llm(prompt, response_model, **kwargs):
        return FeatureLLMResponse.model_validate(
            {
                "features": [
                    {"title": "New1", "description": "d", "importance": 1, "feature_type": "must"},
                    {"title": "New2", "description": "d", "importance": 1, "feature_type": "must"},
                ]
            }
        )

    monkeypatch.setattr(spec_steps, "call_llm", fake_call_llm)

    async with SessionLocal() as session:
        project = await _create_project(session)
        # step completed earlier, so regeneration path used
        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.FEATURES,
            status=StepStatus.COMPLETED,
            approval_status=ApprovalStatus.APPROVED,
            last_approved_at=datetime.now(timezone.utc),
        )
        session.add(step)
        selected = Feature(project_id=project.id, name="Sel", description="d", is_selected=True)
        unselected = Feature(project_id=project.id, name="Unsel", description="d", is_selected=False)
        session.add_all([selected, unselected])
        await session.commit()

        await spec_steps.run_feature_step(session, project.id)

        refreshed_selected = await session.get(Feature, selected.id)
        refreshed_unselected = await session.get(Feature, unselected.id)
        assert refreshed_selected.is_selected is True
        assert refreshed_selected.is_deleted is False
        assert refreshed_unselected.is_deleted is True

        new_feats = (
            await session.execute(
                select(Feature).where(
                    Feature.project_id == project.id, Feature.is_deleted == False  # noqa: E712
                )
            )
        ).scalars().all()
        assert len(new_feats) >= 3  # selected + new ones
        assert all(f.is_selected in (True, False) for f in new_feats)


@pytest.mark.asyncio
async def test_backward_compat_selects_all_if_approved_no_selection(item_client):
    client, SessionLocal = item_client
    async with SessionLocal() as session:
        project = await _create_project(session)
        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.OBJECTIVE,
            status=StepStatus.COMPLETED,
            approval_status=ApprovalStatus.APPROVED,
            last_approved_at=datetime.now(timezone.utc),
        )
        session.add(step)
        obj = ProjectObjective(project_id=project.id, title="O1", text="t1", is_selected=False)
        session.add(obj)
        await session.commit()

    resp = client.get(f"/projects/{project.id}/spec-wizard/detail")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["objectives"][0]["is_selected"] is True

    async with SessionLocal() as session:
        refreshed = await session.get(ProjectObjective, obj.id)
        assert refreshed.is_selected is True
