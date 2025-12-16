from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApprovalStatus, TaskGranularity, TaskStatus
from app.db.base import Base
from app.models.base import BaseModelMixin


class Epic(BaseModelMixin, Base):
    __tablename__ = "epics"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_component_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    related_feature_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    business_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    urgency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_reduction: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    implementation_status: Mapped[str] = mapped_column(String(20), default="not_started")
    estimated_total_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_points: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    last_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="epics")
    dependencies: Mapped[list["EpicDependency"]] = relationship(
        "EpicDependency",
        back_populates="epic",
        cascade="all, delete-orphan",
        foreign_keys="EpicDependency.epic_id",
    )
    reverse_dependencies: Mapped[list["EpicDependency"]] = relationship(
        "EpicDependency",
        back_populates="depends_on",
        cascade="all, delete-orphan",
        foreign_keys="EpicDependency.depends_on_epic_id",
    )
    sprint_epics: Mapped[list["SprintEpic"]] = relationship(
        "SprintEpic", back_populates="epic", cascade="all, delete-orphan"
    )


class EpicDependency(BaseModelMixin, Base):
    __tablename__ = "epic_dependencies"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    epic_id: Mapped[int] = mapped_column(
        ForeignKey("epics.id", ondelete="CASCADE"), nullable=False
    )
    depends_on_epic_id: Mapped[int] = mapped_column(
        ForeignKey("epics.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    epic: Mapped[Epic] = relationship(
        "Epic", foreign_keys=[epic_id], back_populates="dependencies"
    )
    depends_on: Mapped[Epic] = relationship(
        "Epic", foreign_keys=[depends_on_epic_id], back_populates="reverse_dependencies"
    )


class SprintPlan(BaseModelMixin, Base):
    __tablename__ = "sprint_plans"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    last_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="sprint_plans")
    sprints: Mapped[list["Sprint"]] = relationship(
        "Sprint", back_populates="sprint_plan", cascade="all, delete-orphan"
    )


class Sprint(BaseModelMixin, Base):
    __tablename__ = "sprints"

    sprint_plan_id: Mapped[int] = mapped_column(
        ForeignKey("sprint_plans.id", ondelete="CASCADE"), nullable=False
    )
    index: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    duration_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    capacity_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity_sp: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sprint_plan: Mapped[SprintPlan] = relationship("SprintPlan", back_populates="sprints")
    sprint_epics: Mapped[list["SprintEpic"]] = relationship(
        "SprintEpic", back_populates="sprint", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="sprint", cascade="all, delete-orphan"
    )


class SprintEpic(BaseModelMixin, Base):
    __tablename__ = "sprint_epics"

    sprint_id: Mapped[int] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False
    )
    epic_id: Mapped[int] = mapped_column(
        ForeignKey("epics.id", ondelete="CASCADE"), nullable=False
    )
    scope_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    sprint: Mapped[Sprint] = relationship("Sprint", back_populates="sprint_epics")
    epic: Mapped[Epic] = relationship("Epic", back_populates="sprint_epics")


class Task(BaseModelMixin, Base):
    __tablename__ = "tasks"

    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sprint_id: Mapped[int | None] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), nullable=True
    )
    epic_id: Mapped[int | None] = mapped_column(
        ForeignKey("epics.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.TODO, nullable=False
    )
    granularity: Mapped[TaskGranularity | None] = mapped_column(
        Enum(TaskGranularity), nullable=True
    )
    refinement_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acceptance_criteria: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    depends_on_task_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    related_dod_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    related_nfr_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    estimate_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dod_focus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nfr_focus: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    parent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    estimate_sp: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sprint: Mapped[Sprint | None] = relationship("Sprint", back_populates="tasks")
    epic: Mapped[Epic | None] = relationship("Epic")
    parent_task: Mapped["Task"] = relationship(
        "Task", remote_side="Task.id", backref="child_tasks"
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    depends_on_task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
