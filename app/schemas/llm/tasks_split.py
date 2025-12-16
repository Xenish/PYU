from typing import List, Optional

from pydantic import BaseModel


class FineTaskItem(BaseModel):
    parent_task_id: int
    title: str
    description: str
    acceptance_criteria: List[str]
    estimate_sp: Optional[int] = None


class TaskSplitResponse(BaseModel):
    tasks: List[FineTaskItem]
