from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, false

from app.db.base import Base


class BaseModelMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_deleted = Column(Boolean, default=False, server_default=false())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


__all__ = ["Base", "BaseModelMixin"]
