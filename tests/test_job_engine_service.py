import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import JobStatus, JobType
from app.db.base import Base
from app.models.job import Job
from app.models.planning import Sprint, SprintPlan
from app.models.project import Project
from app.services import job_engine


class Dummy:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.mark.asyncio
async def test_job_engine_success(monkeypatch):
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
        await session.commit()

        async def fake_run(db, sp, job_obj):
            await job_engine._update_progress(db, job_obj, 100, "done")  # type: ignore[attr-defined]
            return {"fine_tasks": 1}

        monkeypatch.setattr(job_engine, "_run_task_pipeline_for_sprint", fake_run)

        job = await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict={"p": 1})
        assert job.status == JobStatus.QUEUED.value

        job = await job_engine.start_job(session, job)
        assert job.status == JobStatus.COMPLETED.value
        assert json.loads(job.result_json) == {"fine_tasks": 1}

    await engine.dispose()


@pytest.mark.asyncio
async def test_job_engine_failure(monkeypatch):
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
        await session.commit()

        async def fake_run(db, sp, job_obj):
            raise RuntimeError("boom")

        monkeypatch.setattr(job_engine, "_run_task_pipeline_for_sprint", fake_run)

        job = await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict=None)
        job = await job_engine.start_job(session, job)
        assert job.status == JobStatus.FAILED.value
        assert "boom" in (job.error_message or "")

    await engine.dispose()


@pytest.mark.asyncio
async def test_job_invalid_transition(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        job = Job(
            project_id=1,
            sprint_id=None,
            type=JobType.TASK_PIPELINE_FOR_SPRINT.value,
            status=JobStatus.COMPLETED.value,
            payload_json="{}",
        )
        session.add(job)
        await session.commit()

        with pytest.raises(job_engine.InvalidJobTransition):
            await job_engine.start_job(session, job)

    await engine.dispose()
