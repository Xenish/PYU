import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.project import Project
from app.repositories.project_repo import list_projects, get_project_by_id


@pytest.mark.asyncio
async def test_soft_delete_repo_filters():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        p1 = Project(name="Active", description="d")
        p2 = Project(name="Deleted", description="d", is_deleted=True)
        session.add_all([p1, p2])
        await session.commit()

        active = await list_projects(session)
        assert len(active) == 1
        assert active[0].name == "Active"

        all_projects = await list_projects(session, include_deleted=True)
        assert len(all_projects) == 2

        got = await get_project_by_id(session, p2.id, include_deleted=True)
        assert got is not None

    await engine.dispose()
