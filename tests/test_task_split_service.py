import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import TaskGranularity, TaskStatus
from app.db.base import Base
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan, Task
from app.models.project import Project
from app.services import task_split


@pytest.mark.asyncio
async def test_refine_tasks_pass3_for_sprint(monkeypatch):
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
        session.add(SprintEpic(sprint_id=sprint.id, epic_id=epic.id))
        await session.flush()
        parent = Task(
            project_id=project.id,
            sprint_id=sprint.id,
            epic_id=epic.id,
            title="Medium1",
            description="d",
            status=TaskStatus.TODO,
            granularity=TaskGranularity.MEDIUM,
            refinement_round=2,
        )
        session.add(parent)
        await session.commit()

        async def fake_llm(prompt, response_model, **kwargs):
            return response_model.model_validate(
                {
                    "tasks": [
                        {
                            "parent_task_id": parent.id,
                            "title": "Child1",
                            "description": "fine",
                            "acceptance_criteria": ["a"],
                            "estimate_sp": 2,
                        }
                    ]
                }
            )

        monkeypatch.setattr(task_split, "call_llm", fake_llm)

        fine_tasks = await task_split.refine_tasks_pass3_for_sprint(session, sprint.id)
        assert len(fine_tasks) == 1
        fine = fine_tasks[0]
        assert fine.parent_task_id == parent.id
        assert fine.granularity == TaskGranularity.FINE
        assert fine.status == TaskStatus.READY_FOR_DEV

        # parent should be marked stale
        refreshed_parent = await session.get(Task, parent.id)
        assert refreshed_parent.status == TaskStatus.STALE

        # rerun should not append more children (previous fine tasks soft-deleted)
        fine_tasks_again = await task_split.refine_tasks_pass3_for_sprint(session, sprint.id)
        assert len(fine_tasks_again) == 1

    await engine.dispose()
