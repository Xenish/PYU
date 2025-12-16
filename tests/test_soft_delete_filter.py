import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.db.filters import only_active
from app.models.project import Project


@pytest.mark.asyncio
async def test_soft_delete_filter_excludes_deleted_rows():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        project = Project(name="Active")
        deleted = Project(name="Deleted", is_deleted=True)
        session.add_all([project, deleted])
        await session.commit()

    async with SessionLocal() as session:
        rows_all = (
            await session.execute(select(Project).execution_options(include_deleted=True))
        ).scalars().all()
        assert any(r.is_deleted for r in rows_all)
        result = await session.execute(only_active(select(Project), Project))
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].name == "Active"

        assert len(rows_all) == 2

    await engine.dispose()
