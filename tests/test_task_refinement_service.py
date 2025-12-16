import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import TaskGranularity, TaskStatus
from app.db.base import Base
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan, Task, TaskDependency
from app.models.project import Project
from app.models.quality import DoDItem, NFRItem
from app.services import task_refinement


@pytest.mark.asyncio
async def test_refine_tasks_pass2_for_sprint(monkeypatch):
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
        session.add_all(
            [
                DoDItem(project_id=project.id, category="release_ready", description="Release ready"),
                NFRItem(project_id=project.id, type="performance", description="fast"),
            ]
        )
        await session.flush()
        t1 = Task(
            project_id=project.id,
            sprint_id=sprint.id,
            epic_id=epic.id,
            title="Draft1",
            description="desc",
            status=TaskStatus.TODO,
            granularity=TaskGranularity.COARSE,
            refinement_round=1,
        )
        t2 = Task(
            project_id=project.id,
            sprint_id=sprint.id,
            epic_id=epic.id,
            title="Draft2",
            description="desc2",
            status=TaskStatus.TODO,
            granularity=TaskGranularity.COARSE,
            refinement_round=1,
        )
        session.add_all([t1, t2])
        await session.commit()

        async def fake_llm(prompt, response_model, **kwargs):
            return response_model.model_validate(
                {
                    "tasks": [
                        {
                            "task_id": t1.id,
                            "title": "Refined1",
                            "description": "new desc",
                            "acceptance_criteria": ["a", "b"],
                            "dod_focus": "release_ready",
                            "nfr_focus": ["performance"],
                            "depends_on_task_ids": [t2.id],
                        },
                        {
                            "task_id": t2.id,
                            "title": "Refined2",
                            "description": "new desc2",
                            "acceptance_criteria": ["c"],
                            "depends_on_task_ids": [],
                        },
                    ]
                }
            )

        monkeypatch.setattr(task_refinement, "call_llm", fake_llm)

        tasks = await task_refinement.refine_tasks_pass2_for_sprint(session, sprint)
        assert len(tasks) == 2
        assert all(t.refinement_round == 2 for t in tasks)
        assert all(t.granularity == TaskGranularity.MEDIUM for t in tasks)
        assert tasks[0].acceptance_criteria

        deps = (
            await session.execute(
                Base.metadata.tables["task_dependencies"].select()
            )
        ).all()
        assert len(deps) == 1
        assert deps[0].depends_on_task_id == t2.id

    await engine.dispose()
