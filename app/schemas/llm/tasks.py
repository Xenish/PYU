from typing import List, Optional

from pydantic import BaseModel


class TaskDraftItem(BaseModel):
    title: str
    description: str
    tags: Optional[List[str]] = None


class TaskDraftResponse(BaseModel):
    tasks: List[TaskDraftItem]
