from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobRead(BaseModel):
    id: int
    project_id: int
    sprint_id: Optional[int] = None
    type: str
    status: str
    payload_json: str
    result_json: Optional[str] = None
    error_message: Optional[str] = None
    progress_pct: Optional[int] = None
    current_step: Optional[str] = None
    cancellation_requested: bool = False
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobCreateTaskPipeline(BaseModel):
    project_id: int = Field(..., description="Proje id")
    sprint_id: int = Field(..., description="Sprint id")
