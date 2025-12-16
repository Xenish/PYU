import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import JobStatus, TaskStatus
from app.db.base import Base
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.project import Project
from app.services import job_engine, task_generation, task_refinement, task_split


@pytest.mark.asyncio
async def test_task_pipeline_job_progress(monkeypatch):
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
        await session.commit()

        async def fake_pass1(db, s, job_id=None):
            return [object()]

        async def fake_pass2(db, s, job_id=None):
            return [object()]

        class Dummy:
            def __init__(self):
                self.status = TaskStatus.READY_FOR_DEV

        async def fake_pass3(db, sprint_id, job_id=None):
            return [Dummy()]

        # Patch both services module and job_engine references
        monkeypatch.setattr(task_generation, "generate_draft_tasks_for_sprint", fake_pass1)
        monkeypatch.setattr(task_refinement, "refine_tasks_pass2_for_sprint", fake_pass2)
        monkeypatch.setattr(task_split, "refine_tasks_pass3_for_sprint", fake_pass3)
        monkeypatch.setattr(job_engine, "generate_draft_tasks_for_sprint", fake_pass1)
        monkeypatch.setattr(job_engine, "refine_tasks_pass2_for_sprint", fake_pass2)
        monkeypatch.setattr(job_engine, "refine_tasks_pass3_for_sprint", fake_pass3)

        job = await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict=None)
        job = await job_engine.start_job(session, job)

        assert job.status == JobStatus.COMPLETED.value, job.error_message
        assert job.progress_pct == 100
        assert job.current_step == "completed"

    await engine.dispose()
