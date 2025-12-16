from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.imports import LLMCallLog


async def log_llm_call(
    db: AsyncSession,
    project_id: Optional[int],
    step_type: str,
    status: str,
    request_payload: Any,
    response_payload: Any,
) -> None:
    log = LLMCallLog(
        project_id=project_id,
        step_type=step_type,
        status=status,
        request_payload=request_payload,
        response_payload=response_payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
