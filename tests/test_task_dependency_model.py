import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import TaskGranularity, TaskStatus
from app.db.base import Base
from app.models.planning import Sprint, SprintPlan, Task, TaskDependency
from app.models.project import Project


@pytest.mark.asyncio
async def test_task_dependency_basic_insert():
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
        t1 = Task(
            project_id=project.id,
            sprint_id=sprint.id,
            title="T1",
            status=TaskStatus.TODO,
            granularity=TaskGranularity.COARSE,
            refinement_round=1,
        )
        t2 = Task(
            project_id=project.id,
            sprint_id=sprint.id,
            title="T2",
            status=TaskStatus.TODO,
            granularity=TaskGranularity.COARSE,
            refinement_round=1,
        )
        session.add_all([t1, t2])
        await session.flush()
        dep = TaskDependency(task_id=t2.id, depends_on_task_id=t1.id)
        session.add(dep)
        await session.commit()

        rows = (await session.execute(Base.metadata.tables["task_dependencies"].select())).all()
        assert len(rows) == 1
        assert rows[0].task_id == t2.id
        assert rows[0].depends_on_task_id == t1.id

    await engine.dispose()
