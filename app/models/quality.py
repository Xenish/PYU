from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import TaskStatus
from app.db.base import Base
from app.models.base import BaseModelMixin
from app.models.mixins import EnhancedItemMixin


class DoDItem(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "dod_items"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    test_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    done_when: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_feature_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    related_component_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    implementation_status: Mapped[str] = mapped_column(String(20), default="not_started")
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Decision Support Fields
    priority_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impact_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommendation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    advantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    disadvantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    conflicts_with: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    requires: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    category_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="dod_items")


class NFRItem(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "nfr_items"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    measurable_target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    related_component_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    implementation_status: Mapped[str] = mapped_column(String(20), default="not_started")
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Decision Support Fields
    priority_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impact_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommendation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    advantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    disadvantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    conflicts_with: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    requires: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    category_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="nfr_items")


class RiskItem(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "risk_items"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text)
    impact: Mapped[int] = mapped_column(Integer)
    likelihood: Mapped[int] = mapped_column(Integer)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Decision Support Fields
    priority_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impact_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommendation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    advantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    disadvantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    conflicts_with: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    requires: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    category_exclusive: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="risks")
