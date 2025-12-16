from typing import List, Optional

from pydantic import BaseModel, Field


class ObjectiveItem(BaseModel):
    title: str
    description: str
    priority: int = Field(ge=1, le=10)
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


class ObjectiveLLMResponse(BaseModel):
    objectives: List[ObjectiveItem]
