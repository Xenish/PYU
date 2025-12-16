# Observability

## Logging

- JSON format with context fields:
  ```json
  {
    "ts": "...",
    "level": "INFO",
    "msg": "request.start",
    "logger": "masper.api",
    "request_id": "req-abc123",
    "project_id": 1,
    "job_id": 42,
    "component": "api",
    "path": "/health"
  }
  ```
- Context comes from middleware/job runner/LLM adapter. `X-Request-ID` header is set per request.

## Metrics

- Exposed at `GET /metrics` (Prometheus text format).
- Key metrics:
  - `masper_api_requests_total{path,method,status}`
  - `masper_api_request_duration_seconds{path,method}`
  - `masper_jobs_total{type,status}`, `masper_jobs_in_progress{type}`
  - `masper_llm_calls_total{intent,outcome}`

## Status & Diagnostics

- `GET /status/overview`: system summary (projects count, jobs by status, today’s LLM calls).
- `GET /projects/{id}/diagnostics`: project-level counts (epics/sprints/tasks), last wizard run, last task pipeline job.

These endpoints give quick health insight without opening the UI.***
