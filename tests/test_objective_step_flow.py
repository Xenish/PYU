import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import StepStatus, StepType
from app.db.base import Base
from app.models.project import Project, ProjectObjective, ProjectStep
from app.services import objective_step


@pytest.mark.asyncio
async def test_objective_flow(monkeypatch):
    # Fake LLM response
    async def fake_llm(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None):
        return response_model.model_validate(
            {"objectives": [{"title": "Obj1", "description": "Desc1", "priority": 1}]}
        )

    monkeypatch.setattr(objective_step, "call_llm", fake_llm)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Proj", description="D")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        objs = await objective_step.run_objective_step(session, project.id)
        assert len(objs) == 1
        assert objs[0].title == "Obj1"

        step_res = await session.execute(
            select(ProjectStep).where(
                ProjectStep.project_id == project.id, ProjectStep.step_type == StepType.OBJECTIVE
            )
        )
        step = step_res.scalars().first()
        assert step.status == StepStatus.COMPLETED
        assert step.last_ai_run_at is not None

        obj_rows = (await session.execute(select(ProjectObjective))).scalars().all()
        assert len(obj_rows) == 1

    await engine.dispose()
