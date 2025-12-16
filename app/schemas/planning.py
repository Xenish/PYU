from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EpicRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str] = None
    story_points: Optional[int] = None

    model_config = {"from_attributes": True}


class EpicDependencyRead(BaseModel):
    epic_id: int
    depends_on_epic_id: int

    model_config = {"from_attributes": True}


class SprintRead(BaseModel):
    id: int
    index: int
    name: str
    status: str
    capacity_sp: Optional[int] = None

    model_config = {"from_attributes": True}


class SprintPlanRead(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SprintEpicRead(BaseModel):
    sprint_id: int
    epic_id: int

    model_config = {"from_attributes": True}


class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    epic_name: Optional[str] = None
    granularity: Optional[str] = None
    refinement_round: Optional[int] = None
    order_index: Optional[int] = None
    sprint_id: Optional[int] = None
    epic_id: Optional[int] = None
    acceptance_criteria: Optional[list[str]] = None
    dod_focus: Optional[str] = None
    nfr_focus: Optional[list[str]] = None
    parent_task_id: Optional[int] = None
    estimate_sp: Optional[int] = None

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    status: str


class PlanningEpicOverview(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    story_points: Optional[int] = None
    sprint_ids: list[int] = Field(default_factory=list)
    dependencies: list[int | None] = Field(default_factory=list)
    quality_tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PlanningSprintOverview(BaseModel):
    id: int
    name: str
    capacity_sp: Optional[int] = None
    allocated_sp: int = 0
    epic_ids: list[int] = Field(default_factory=list)
    quality_summary: dict = Field(default_factory=dict)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanningOverview(BaseModel):
    project_id: int
    epics: list[PlanningEpicOverview]
    sprints: list[PlanningSprintOverview]
