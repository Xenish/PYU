import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import StepStatus, StepType
from app.db.base import Base
from app.models.project import Project
from app.services import quality_steps
from app.services.project_steps import get_or_create_step


@pytest.mark.asyncio
async def test_run_quality_steps(monkeypatch):
    async def fake_llm(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {
                "dod_items": [{"description": "DoD", "category": "functional", "priority": 1}],
                "nfr_items": [{"type": "performance", "description": "fast"}],
                "risks": [{"description": "Risk", "impact": 1, "likelihood": 1}],
            }
        )

    monkeypatch.setattr(quality_steps, "call_llm", fake_llm)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="ProjQ", description="DQ")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        dod, nfr, risks = await quality_steps.run_quality_steps(session, project.id)
        assert len(dod) == 1
        assert len(nfr) == 1
        assert len(risks) == 1
        step = await get_or_create_step(session, project.id, StepType.DOD)
        assert step.status == StepStatus.COMPLETED

    await engine.dispose()
