from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class ImportSession(BaseModelMixin, Base):
    __tablename__ = "import_sessions"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="created")
    source_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="import_sessions")
    assets: Mapped[list["ImportedAsset"]] = relationship(
        "ImportedAsset", back_populates="import_session", cascade="all, delete-orphan"
    )
    summaries: Mapped[list["ImportedSummary"]] = relationship(
        "ImportedSummary", back_populates="import_session", cascade="all, delete-orphan"
    )
    gap_results: Mapped[list["GapAnalysisResult"]] = relationship(
        "GapAnalysisResult", back_populates="import_session", cascade="all, delete-orphan"
    )


class ImportedAsset(BaseModelMixin, Base):
    __tablename__ = "imported_assets"

    import_session_id: Mapped[int] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    import_session: Mapped[ImportSession] = relationship(
        "ImportSession", back_populates="assets"
    )


class ImportedSummary(BaseModelMixin, Base):
    __tablename__ = "imported_summaries"

    import_session_id: Mapped[int] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"), nullable=False
    )
    raw_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("imported_assets.id", ondelete="SET NULL"), nullable=True
    )

    import_session: Mapped[ImportSession] = relationship(
        "ImportSession", back_populates="summaries"
    )
    related_asset: Mapped["ImportedAsset | None"] = relationship("ImportedAsset")


class ProjectSpecSnapshot(BaseModelMixin, Base):
    __tablename__ = "project_spec_snapshots"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    spec_version: Mapped[int] = mapped_column(Integer, default=1)
    spec_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship("Project")


class GapAnalysisResult(BaseModelMixin, Base):
    __tablename__ = "gap_analysis_results"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    import_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="SET NULL"), nullable=True
    )
    snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_spec_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    result_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship("Project")
    import_session: Mapped["ImportSession | None"] = relationship(
        "ImportSession", back_populates="gap_results"
    )
    snapshot: Mapped["ProjectSpecSnapshot | None"] = relationship("ProjectSpecSnapshot")


class Comment(BaseModelMixin, Base):
    __tablename__ = "comments"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="comments")


class LLMCallLog(BaseModelMixin, Base):
    __tablename__ = "llm_call_logs"

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    step_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped["Project | None"] = relationship(
        "Project", back_populates="llm_call_logs"
    )
