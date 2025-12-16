from typing import List, Optional

from pydantic import BaseModel, field_validator


class ArchitectureComponentItem(BaseModel):
    name: str
    layer: str  # frontend | backend | infra | data | shared
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
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

    @field_validator("conflicts_with", "requires", mode="before")
    @classmethod
    def _sanitize_int_list(cls, value):
        """Coerce LLM outputs to int lists; ignore non-numeric entries."""
        if value is None:
            return value
        if not isinstance(value, list):
            return None
        cleaned: list[int] = []
        for item in value:
            if isinstance(item, int):
                cleaned.append(item)
            elif isinstance(item, str) and item.strip().isdigit():
                cleaned.append(int(item.strip()))
        return cleaned or None


class ArchitectureLLMResponse(BaseModel):
    components: List[ArchitectureComponentItem]
