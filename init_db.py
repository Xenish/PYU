"""Initialize the database by creating all tables."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401 - Import all models to register them


async def init_db():
    """Create all database tables."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✓ Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
