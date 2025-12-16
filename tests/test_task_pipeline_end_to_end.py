import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import TaskGranularity, TaskStatus
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan, Task
from app.models.project import Project
from app.models.quality import DoDItem, NFRItem
from app.services import task_generation, task_refinement, task_split


@pytest.fixture
def pipeline_client():
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
    yield client, SessionLocal
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.mark.asyncio
async def test_task_pipeline_pass1_to_pass3(pipeline_client, monkeypatch):
    client, SessionLocal = pipeline_client

    # pass1 fake
    async def fake_llm_pass1(prompt, response_model, **kwargs):
        return response_model.model_validate(
            {"tasks": [{"title": "Draft1", "description": "d1"}, {"title": "Draft2", "description": "d2"}]}
        )

    monkeypatch.setattr(task_generation, "call_llm", fake_llm_pass1)

    async def seed():
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
            session.add(DoDItem(project_id=project.id, category="release_ready", description="Release ready"))
            session.add(NFRItem(project_id=project.id, type="performance", description="fast"))
            await session.commit()
            return sprint.id

    sprint_id = await seed()

    # Pass1
    resp1 = client.post(f"/sprints/{sprint_id}/tasks/generate-draft")
    assert resp1.status_code == 200

    # fetch tasks to know ids
    async with SessionLocal() as session:
        pass1_tasks = (
            await session.execute(
                Base.metadata.tables["tasks"].select().where(Base.metadata.tables["tasks"].c.sprint_id == sprint_id)
            )
        ).all()
        ids = [row.id for row in pass1_tasks]

    # pass2 fake uses ids
    async def fake_llm_pass2(prompt, response_model, **kwargs):
        return response_model.model_validate(
            {
                "tasks": [
                    {
                        "task_id": ids[0],
                        "title": "Medium1",
                        "description": "md1",
                        "acceptance_criteria": ["a"],
                        "dod_focus": "release_ready",
                        "nfr_focus": ["performance"],
                        "depends_on_task_ids": [],
                    },
                    {
                        "task_id": ids[1],
                        "title": "Medium2",
                        "description": "md2",
                        "acceptance_criteria": ["b"],
                        "depends_on_task_ids": [ids[0]],
                    },
                ]
            }
        )

    monkeypatch.setattr(task_refinement, "call_llm", fake_llm_pass2)
    resp2 = client.post(f"/sprints/{sprint_id}/tasks/refine-pass2")
    assert resp2.status_code == 200

    # pass3 fake referencing medium tasks (same ids)
    async def fake_llm_pass3(prompt, response_model, **kwargs):
        return response_model.model_validate(
            {
                "tasks": [
                    {
                        "parent_task_id": ids[0],
                        "title": "Fine1",
                        "description": "fd1",
                        "acceptance_criteria": ["c"],
                        "estimate_sp": 2,
                    }
                ]
            }
        )

    monkeypatch.setattr(task_split, "call_llm", fake_llm_pass3)
    resp3 = client.post(f"/sprints/{sprint_id}/tasks/refine-pass3")
    assert resp3.status_code == 200
    fine_tasks = resp3.json()
    assert len(fine_tasks) == 1
    assert fine_tasks[0]["status"] == TaskStatus.READY_FOR_DEV.value
    assert fine_tasks[0]["parent_task_id"] == ids[0]

    # ready_for_dev filter
    resp_ready = client.get(f"/sprints/{sprint_id}/tasks", params={"ready_for_dev_only": True})
    assert resp_ready.status_code == 200
    assert len(resp_ready.json()) == 1

    # parent tasks stale
    async with SessionLocal() as session:
        parent = await session.get(Task, ids[0])
        assert parent.status == TaskStatus.STALE
        fine = (
            await session.execute(
                Base.metadata.tables["tasks"]
                .select()
                .where(Base.metadata.tables["tasks"].c.refinement_round == 3)
            )
        ).all()
        assert fine[0].granularity == TaskGranularity.FINE
