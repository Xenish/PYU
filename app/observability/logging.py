import json
import logging
from contextvars import ContextVar
from datetime import datetime
from typing import Any
from uuid import uuid4


request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
project_id_var: ContextVar[int | None] = ContextVar("project_id", default=None)
job_id_var: ContextVar[int | None] = ContextVar("job_id", default=None)
component_var: ContextVar[str | None] = ContextVar("component", default=None)


def set_context(
    *,
    request_id: str | None = None,
    project_id: int | None = None,
    job_id: int | None = None,
    component: str | None = None,
) -> None:
    if request_id is not None:
        request_id_var.set(request_id)
    if project_id is not None:
        project_id_var.set(project_id)
    if job_id is not None:
        job_id_var.set(job_id)
    if component is not None:
        component_var.set(component)


def clear_context() -> None:
    request_id_var.set(None)
    project_id_var.set(None)
    job_id_var.set(None)
    component_var.set(None)


def generate_request_id() -> str:
    return f"req-{uuid4().hex[:12]}"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: dict[str, Any] = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or request_id_var.get(),
            "project_id": getattr(record, "project_id", None) or project_id_var.get(),
            "job_id": getattr(record, "job_id", None) or job_id_var.get(),
            "component": getattr(record, "component", None) or component_var.get(),
        }
        # include extra known keys if present
        if hasattr(record, "path"):
            payload["path"] = getattr(record, "path")
        if hasattr(record, "intent"):
            payload["intent"] = getattr(record, "intent")
        return json.dumps(payload, ensure_ascii=False)


def init_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def get_logger(name: str, *, component: str | None = None) -> logging.LoggerAdapter:
    base = logging.getLogger(name)
    if component:
        component_var.set(component)
    return logging.LoggerAdapter(
        base,
        {
            "component": component,
            "request_id": request_id_var.get(),
            "project_id": project_id_var.get(),
            "job_id": job_id_var.get(),
        },
    )
