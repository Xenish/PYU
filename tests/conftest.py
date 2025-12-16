import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - register models
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.services import llm_adapter


@pytest.fixture
def test_app():
    # Use a temp SQLite file to allow multiple connections
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    database_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(database_url, future=True)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(init_models())

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with SessionLocal() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client

    asyncio.get_event_loop().run_until_complete(engine.dispose())
    os.remove(db_path)


@pytest.fixture
def llm_dummy(monkeypatch):
    async def fake_raw(prompt: str, provider: str, model: str, temperature: float | None, max_tokens: int | None):
        return '{"objectives":[{"title":"Test Obj","description":"Desc","priority":1}]}'

    monkeypatch.setattr(llm_adapter, "_raw_llm_call", fake_raw)
