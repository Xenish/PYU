import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import TaskGranularity, TaskStatus
from app.db.base import Base
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.services import task_generation


@pytest.mark.asyncio
async def test_generate_draft_tasks_for_epic(monkeypatch):
    async def fake_llm(prompt, response_model, **kwargs):
        return response_model.model_validate(
            {"tasks": [{"title": "Task1", "description": "Desc"}, {"title": "Task2", "description": "Desc2"}]}
        )

    monkeypatch.setattr(task_generation, "call_llm", fake_llm)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="P", description="D")
        session.add(project)
        await session.flush()
        plan = SprintPlan(project_id=project.id, name="Plan")
        session.add(plan)
        await session.flush()
        sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1")
        session.add(sprint)
        await session.flush()
        epic = Epic(project_id=project.id, name="E1")
        session.add(epic)
        await session.flush()
        se = SprintEpic(sprint_id=sprint.id, epic_id=epic.id)
        session.add(se)
        await session.commit()

        tasks = await task_generation.generate_draft_tasks_for_epic(session, epic, sprint)
        assert len(tasks) == 2
        assert tasks[0].granularity == TaskGranularity.COARSE
        assert tasks[0].status == TaskStatus.TODO

    await engine.dispose()
