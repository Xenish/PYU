from typing import List, Optional

from pydantic import BaseModel, Field


class FeatureItem(BaseModel):
    title: str
    description: Optional[str] = None
    importance: int = Field(ge=1, le=5)
    feature_type: str = "must"  # must | optional
    group: Optional[str] = None
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


class FeatureLLMResponse(BaseModel):
    features: List[FeatureItem]
