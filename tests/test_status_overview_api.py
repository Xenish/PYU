import asyncio
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.project import Project
from app.models.planning import SprintPlan, Sprint, Epic, Task
from app.models.job import Job
from app.core.enums import JobStatus, JobType, TaskStatus


def setup_app():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init_models())
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, SessionLocal


def test_status_endpoints():
    client, SessionLocal = setup_app()
    async def seed():
        async with SessionLocal() as session:
            project = Project(name="P", description="D")
            session.add(project)
            await session.flush()
            plan = SprintPlan(project_id=project.id, name="Plan")
            session.add(plan)
            await session.flush()
            sprint = Sprint(sprint_plan_id=plan.id, index=1, name="S1", status="planned")
            session.add(sprint)
            epic = Epic(project_id=project.id, name="E1", description="d")
            session.add(epic)
            await session.flush()
            task = Task(
                project_id=project.id,
                sprint_id=sprint.id,
                epic_id=epic.id,
                title="T1",
                status=TaskStatus.TODO,
            )
            session.add(task)
            job = Job(
                project_id=project.id,
                sprint_id=sprint.id,
                type=JobType.TASK_PIPELINE_FOR_SPRINT.value,
                status=JobStatus.COMPLETED.value,
                finished_at=datetime.utcnow(),
                payload_json="{}",
            )
            session.add(job)
            await session.commit()
            return project.id, sprint.id

    project_id, sprint_id = asyncio.get_event_loop().run_until_complete(seed())

    ov = client.get("/status/overview")
    assert ov.status_code == 200
    data = ov.json()
    assert data["projects_count"] == 1

    diag = client.get(f"/projects/{project_id}/diagnostics")
    assert diag.status_code == 200
    detail = diag.json()
    assert detail["project_id"] == project_id
    assert detail["epic_count"] == 1
    assert detail["task_count"]["todo"] == 1

    # ensure job exists
    async def count_jobs():
        async with SessionLocal() as session:
            res = await session.execute(select(Job))
            return len(res.scalars().all())
    assert asyncio.get_event_loop().run_until_complete(count_jobs()) == 1
