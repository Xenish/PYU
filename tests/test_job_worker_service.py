import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import JobStatus
from app.db.base import Base
from app.models.planning import Sprint, SprintPlan
from app.models.job import Job
from app.models.project import Project
from app.services import job_engine, job_worker


@pytest.mark.asyncio
async def test_process_next_job_none_when_queue_empty():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        job = await job_worker.process_next_job(session)
        assert job is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_process_next_job_completes(monkeypatch):
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

        async def fake_run(db, sprint, job):
            await job_engine._update_progress(db, job, 50, "pass1")  # type: ignore[attr-defined]
            await job_engine._update_progress(db, job, 100, "completed")  # type: ignore[attr-defined]
            return {"ok": 1}

        monkeypatch.setattr(job_engine, "_run_task_pipeline_for_sprint", fake_run)

        await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict=None)
        job = await job_worker.process_next_job(session)
        assert job is not None
        assert job.status == JobStatus.COMPLETED.value
        assert job.progress_pct == 100

    await engine.dispose()


@pytest.mark.asyncio
async def test_process_next_job_cancel_requested(monkeypatch):
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

        job = await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict=None)
        job.cancellation_requested = True
        await session.commit()

        job = await job_worker.process_next_job(session)
        assert job is not None
        assert job.status == JobStatus.CANCELLED.value

    await engine.dispose()


@pytest.mark.asyncio
async def test_run_worker_loop_processes_job(monkeypatch):
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
            return {"ok": 1}

        monkeypatch.setattr(job_engine, "_run_task_pipeline_for_sprint", fake_run)

        await job_engine.create_job_for_task_pipeline(session, project, sprint, payload_dict=None)
        await job_worker.run_worker_loop(session, max_jobs=5)

        jobs = (
            await session.execute(Job.__table__.select())  # type: ignore[attr-defined]
        ).all()
        assert jobs
        assert jobs[0].status == JobStatus.COMPLETED.value

    await engine.dispose()


@pytest.mark.asyncio
async def test_run_worker_loop_no_jobs():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        await job_worker.run_worker_loop(session)
    await engine.dispose()
