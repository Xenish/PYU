from typing import List, Optional

from pydantic import BaseModel, Field


class DoDItemModel(BaseModel):
    description: str
    category: str  # functional | non_functional | process
    test_method: Optional[str] = None
    done_when: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)
    priority_score: Optional[int] = None
    impact_level: Optional[str] = None
    recommendation_type: Optional[str] = None
    category_tags: Optional[list[str]] = None
    rationale: Optional[str] = None
    advantages: Optional[list[str]] = None
    disadvantages: Optional[list[str]] = None
    conflicts_with: Optional[list[int]] = None
    requires: Optional[list[int]] = None
    category_exclusive: Optional[bool] = None


class NFRItemModel(BaseModel):
    type: str  # performance | security | reliability | ux | observability | other
    description: str
    measurable_target: Optional[str] = None
    priority_score: Optional[int] = None
    impact_level: Optional[str] = None
    recommendation_type: Optional[str] = None
    category_tags: Optional[list[str]] = None
    rationale: Optional[str] = None
    advantages: Optional[list[str]] = None
    disadvantages: Optional[list[str]] = None
    conflicts_with: Optional[list[int]] = None
    requires: Optional[list[int]] = None
    category_exclusive: Optional[bool] = None


class RiskItemModel(BaseModel):
    description: str
    impact: int = Field(ge=1, le=5)
    likelihood: int = Field(ge=1, le=5)
    mitigation: Optional[str] = None
    priority_score: Optional[int] = None
    impact_level: Optional[str] = None
    recommendation_type: Optional[str] = None
    category_tags: Optional[list[str]] = None
    rationale: Optional[str] = None
    advantages: Optional[list[str]] = None
    disadvantages: Optional[list[str]] = None
    conflicts_with: Optional[list[int]] = None
    requires: Optional[list[int]] = None
    category_exclusive: Optional[bool] = None


class QualityLLMResponse(BaseModel):
    dod_items: List[DoDItemModel]
    nfr_items: List[NFRItemModel]
    risks: List[RiskItemModel]
