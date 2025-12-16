from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class RefinedTaskItem(BaseModel):
    task_id: int = Field(..., description="Pass 1'de üretilen task id'si")
    title: str
    description: str
    acceptance_criteria: List[str]
    dod_focus: Optional[str] = None
    nfr_focus: Optional[List[str]] = None
    depends_on_task_ids: Optional[List[int]] = None

    @field_validator("depends_on_task_ids")
    @classmethod
    def uniq_depends(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is None:
            return value
        # remove duplicates while preserving order
        seen = set()
        deduped = []
        for item in value:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped


class TaskRefinementResponse(BaseModel):
    tasks: List[RefinedTaskItem]
