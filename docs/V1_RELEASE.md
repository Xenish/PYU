# V1 Release Notes

## What it solves
- Guided Spec Wizard (Objective, TechStack, Features, Architecture, Quality).
- Epic/Sprint planning with capacity + quality summaries.
- 3-pass task pipeline (draft → refine → ready-for-dev).
- Job/LLM infrastructure (quota, retry, logs, metrics).
- Operator console: jobs/tasks, spec wizard, planning view, task board, status.

## What’s included
- Backend: FastAPI + SQLAlchemy async, Alembic migrations, LLM adapter with quota/retry/logging, job engine/worker, planning/task pipeline APIs, observability endpoints (`/metrics`, `/status/overview`, project diagnostics).
- Frontend: Next.js console with tabs (Jobs & Tasks, Spec Wizard, Planning, Status), sprint task board, planning overview tables, status panels.
- Observability: JSON logs with request/job context, Prometheus metrics, status/diagnostics APIs.

## What’s NOT included (conscious omissions)
- Auth/RBAC or multi-tenant org model.
- Production-grade queue/worker scaling (single-process assumption).
- Full Jira/Trello UX (basic board only).
- Strict rate-limiting / billing; LLM provider remains “dummy” by default.

## Future ideas (V2+)
- Multi-user / workspace model with auth.
- Real LLM provider + cost-aware quotas.
- Richer visuals (Gantt/graph) for planning and task dependencies.
- Background workers with distributed locks, retry DLQ.

## Quick start
See `docs/GETTING_STARTED.md` for setup, env examples, and the end-to-end “happy path” flow (project → wizard → plan → task pipeline → UI → observability).
