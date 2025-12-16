from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatusOverview(BaseModel):
    projects_count: int
    jobs: dict
    llm_calls_today: int
    llm_quota_limit: Optional[int] = None


class ProjectDiagnostics(BaseModel):
    project_id: int
    epic_count: int
    sprint_count: int
    task_count: dict
    last_wizard_run_at: Optional[datetime] = None
    last_task_pipeline_job: Optional[dict] = None


class LLMInfo(BaseModel):
    provider: str
    model: str
    available_models: list[str]


class LLMUpdate(BaseModel):
    model: str
    provider: str | None = None
