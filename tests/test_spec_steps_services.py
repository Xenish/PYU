import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import StepStatus, StepType
from app.db.base import Base
from app.models.project import Project, ProjectStep
from app.services import spec_steps
from app.services.project_steps import get_or_create_step
from app.core.enums import StepType, StepStatus


@pytest.mark.asyncio
async def test_run_tech_stack_step(monkeypatch):
    async def fake_llm(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"items": [{"category": "backend", "name": "FastAPI"}]}
        )

    monkeypatch.setattr(spec_steps, "call_llm", fake_llm)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Proj", description="D")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        options = await spec_steps.run_tech_stack_step(session, project.id)
        assert len(options) == 1

        step = await get_or_create_step(session, project.id, step_type=StepType.TECH_STACK)
        assert step.status == StepStatus.COMPLETED

    await engine.dispose()


@pytest.mark.asyncio
async def test_run_feature_and_architecture_steps(monkeypatch):
    async def fake_llm_feature(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"features": [{"title": "F1", "description": "d", "importance": 3, "feature_type": "must"}]}
        )

    async def fake_llm_arch(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"components": [{"name": "API", "layer": "backend", "responsibilities": ["r1"]}]}
        )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Proj2", description="D2")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        monkeypatch.setattr(spec_steps, "call_llm", fake_llm_feature)
        feats = await spec_steps.run_feature_step(session, project.id)
        assert len(feats) == 1
        step_feat = await get_or_create_step(session, project.id, StepType.FEATURES)
        assert step_feat.status == StepStatus.COMPLETED

        monkeypatch.setattr(spec_steps, "call_llm", fake_llm_arch)
        comps = await spec_steps.run_architecture_step(session, project.id)
        assert len(comps) == 1
        step_arch = await get_or_create_step(session, project.id, StepType.ARCHITECTURE)
        assert step_arch.status == StepStatus.COMPLETED

    await engine.dispose()
