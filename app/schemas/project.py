from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import PlanningDetailLevel, ProjectStatus, StepStatus, StepType


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    planning_detail_level: PlanningDetailLevel = PlanningDetailLevel.LOW
    language: str = "tr"


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    status: ProjectStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    planning_detail_level: PlanningDetailLevel | None = None
    language: str | None = None


class ProjectStepBase(BaseModel):
    step_type: StepType
    status: StepStatus = StepStatus.PLANNED
    last_input_hash: Optional[str] = None
    last_output_json: Optional[dict] = None


class ProjectStepCreate(ProjectStepBase):
    pass


class ProjectStepRead(ProjectStepBase):
    id: int
    project_id: int

    model_config = {"from_attributes": True}


class ProjectSuggestionRead(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    examples: list[str] | None
    user_added_examples: list[str] | None
    is_selected: bool
    generation_round: int

    # Decision support
    priority_score: int | None
    impact_level: str | None
    recommendation_type: str | None
    category_tags: list[str] | None
    rationale: str | None
    advantages: list[str] | None
    disadvantages: list[str] | None

    model_config = {"from_attributes": True}


class ProjectReviewItem(BaseModel):
    suggestion_title: str
    is_adequate: bool
    feedback: str | None
    new_questions: list[str] | None


class ProjectReviewResponse(BaseModel):
    reviews: list[ProjectReviewItem]
    new_suggestions: list[ProjectSuggestionRead]
    overall_feedback: str
