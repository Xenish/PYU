import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.services.llm_policy import LLMQuotaExceeded, check_and_increment_project_quota


@pytest.mark.asyncio
async def test_project_quota_enforced():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        # allow 2 calls
        await check_and_increment_project_quota(session, project_id=1, max_calls=2)
        await check_and_increment_project_quota(session, project_id=1, max_calls=2)
        with pytest.raises(LLMQuotaExceeded):
            await check_and_increment_project_quota(session, project_id=1, max_calls=2)

    await engine.dispose()
