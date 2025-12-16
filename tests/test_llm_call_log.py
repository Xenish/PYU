import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.imports import LLMCallLog
from app.models.project import Project
from app.services import llm_adapter


@pytest.mark.asyncio
async def test_llm_call_logs_success(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def fake_raw(prompt: str, provider: str, model: str, temperature, max_tokens):
        return '{"foo":"bar"}'

    monkeypatch.setattr(llm_adapter, "_raw_llm_call", fake_raw)

    class RespModel(llm_adapter.BaseModel):
        foo: str

    async with SessionLocal() as session:
        project = Project(name="P", description="D")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        resp = await llm_adapter.call_llm(
            "prompt", RespModel, db=session, project_id=project.id, step_type="TEST"
        )
        assert resp.foo == "bar"
        logs = (await session.execute(LLMCallLog.__table__.select())).fetchall()
        assert len(logs) == 1
        assert logs[0].status == "success"

    await engine.dispose()
