from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApprovalStatus, PlanningDetailLevel, ProjectStatus, StepStatus, StepType
from app.db.base import Base
from app.models.base import BaseModelMixin
from app.models.mixins import EnhancedItemMixin


class Project(BaseModelMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False
    )
    language: Mapped[str] = mapped_column(String(5), default="tr")
    planning_detail_level: Mapped[PlanningDetailLevel] = mapped_column(
        Enum(PlanningDetailLevel), default=PlanningDetailLevel.LOW, nullable=False
    )
    current_snapshot_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origin_project_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spec_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spec_locked_at = Column(DateTime(timezone=True), nullable=True)

    steps: Mapped[list["ProjectStep"]] = relationship(
        "ProjectStep", back_populates="project", cascade="all, delete-orphan"
    )
    objectives: Mapped[list["ProjectObjective"]] = relationship(
        "ProjectObjective", back_populates="project", cascade="all, delete-orphan"
    )
    tech_stack_options: Mapped[list["TechStackOption"]] = relationship(
        "TechStackOption", back_populates="project", cascade="all, delete-orphan"
    )
    features: Mapped[list["Feature"]] = relationship(
        "Feature", back_populates="project", cascade="all, delete-orphan"
    )
    architecture_components: Mapped[list["ArchitectureComponent"]] = relationship(
        "ArchitectureComponent", back_populates="project", cascade="all, delete-orphan"
    )
    dod_items: Mapped[list["DoDItem"]] = relationship(
        "DoDItem", back_populates="project", cascade="all, delete-orphan"
    )
    nfr_items: Mapped[list["NFRItem"]] = relationship(
        "NFRItem", back_populates="project", cascade="all, delete-orphan"
    )
    risks: Mapped[list["RiskItem"]] = relationship(
        "RiskItem", back_populates="project", cascade="all, delete-orphan"
    )
    epics: Mapped[list["Epic"]] = relationship(
        "Epic", back_populates="project", cascade="all, delete-orphan"
    )
    sprint_plans: Mapped[list["SprintPlan"]] = relationship(
        "SprintPlan", back_populates="project", cascade="all, delete-orphan"
    )
    import_sessions: Mapped[list["ImportSession"]] = relationship(
        "ImportSession", back_populates="project", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="project", cascade="all, delete-orphan"
    )
    llm_call_logs: Mapped[list["LLMCallLog"]] = relationship(
        "LLMCallLog", back_populates="project", cascade="all, delete-orphan"
    )
    suggestions: Mapped[list["ProjectSuggestion"]] = relationship(
        "ProjectSuggestion", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectStep(BaseModelMixin, Base):
    __tablename__ = "project_steps"
    __table_args__ = (
        UniqueConstraint("project_id", "step_type", name="uq_project_step_type"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    step_type: Mapped[StepType] = mapped_column(Enum(StepType), nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus), default=StepStatus.PLANNED, nullable=False
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    last_input_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_ai_run_at = Column(DateTime(timezone=True), nullable=True)
    last_approved_at = Column(DateTime(timezone=True), nullable=True)
    depends_on_step_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="steps")


class ProjectObjective(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "project_objectives"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    v1_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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

    project: Mapped[Project] = relationship("Project", back_populates="objectives")


class TechStackOption(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "tech_stack_options"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    frontend: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    backend: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    database: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    infra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analytics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ci_cd: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pros: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    cons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    project: Mapped[Project] = relationship("Project", back_populates="tech_stack_options")


class Feature(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "features"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="must")
    origin: Mapped[str] = mapped_column(String(20), default="user")
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iteration_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

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

    project: Mapped[Project] = relationship("Project", back_populates="features")


class ArchitectureComponent(EnhancedItemMixin, BaseModelMixin, Base):
    __tablename__ = "architecture_components"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255))
    layer: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    related_feature_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
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

    project: Mapped[Project] = relationship(
        "Project", back_populates="architecture_components"
    )


class ProjectSuggestion(EnhancedItemMixin, BaseModelMixin, Base):
    """AI-generated suggestions for project creation phase."""
    __tablename__ = "project_suggestions"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    examples: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    user_added_examples: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Examples user added to project
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_round: Mapped[int] = mapped_column(Integer, default=1)

    # Inherited from EnhancedItemMixin:
    # priority_score, impact_level, recommendation_type, category_tags,
    # rationale, advantages, disadvantages, conflicts_with, requires, category_exclusive

    project: Mapped[Project] = relationship("Project", back_populates="suggestions")
