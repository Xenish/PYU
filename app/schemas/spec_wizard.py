from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.core.enums import ApprovalStatus, StepStatus, StepType


class StepSummary(BaseModel):
    step_type: StepType
    status: StepStatus
    approval_status: Optional[ApprovalStatus] = None
    last_ai_run_at: Optional[datetime] = None
    last_approved_at: Optional[datetime] = None
    summary: Optional[str] = None
    item_count: int = 0

    model_config = {"from_attributes": True}


class WizardSummary(BaseModel):
    project_id: int
    steps: List[StepSummary]


class ObjectiveDetail(BaseModel):
    id: int
    title: str
    text: str | None
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class TechStackDetail(BaseModel):
    id: int
    frontend: dict | None
    backend: dict | None
    database: dict | None
    infra: dict | None
    analytics: dict | None
    ci_cd: dict | None
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class FeatureDetail(BaseModel):
    id: int
    name: str
    description: str | None
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class ArchitectureDetail(BaseModel):
    id: int
    name: str
    layer: str
    description: str | None
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class DoDDetail(BaseModel):
    id: int
    description: str
    category: str | None
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class NFRDetail(BaseModel):
    id: int
    type: str
    description: str
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class RiskDetail(BaseModel):
    id: int
    description: str
    is_selected: bool
    priority_score: int | None = None
    impact_level: str | None = None
    recommendation_type: str | None = None
    category_tags: list[str] | None = None
    rationale: str | None = None
    advantages: list[str] | None = None
    disadvantages: list[str] | None = None
    conflicts_with: list[int] | None = None
    requires: list[int] | None = None
    category_exclusive: bool = False


class WizardDetail(BaseModel):
    project_id: int
    objectives: List[ObjectiveDetail]
    tech_stack: List[TechStackDetail]
    features: List[FeatureDetail]
    architecture: List[ArchitectureDetail]
    dod_items: List[DoDDetail]
    nfr_items: List[NFRDetail]
    risk_items: List[RiskDetail]
