# Getting Started (V1)

## Backend
1) Python venv:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Environment:
- Copy `.env.example` to `.env` and adjust values (sqlite default works).
3) Database:
```
alembic upgrade head
```
4) Run API:
```
uvicorn app.main:app --reload
```
Health: `GET /health` (DB check) or `GET /health/ping`.

## Frontend
1) Install:
```
cd frontend
npm install
```
2) Environment:
- Copy `.env.local.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE_URL` (default http://localhost:8000).
3) Run:
```
npm run dev
```
UI: http://localhost:3000

## Happy Path Demo
1) Create project via UI (Project selector) or API `POST /projects`.
2) Run Spec Wizard steps from UI (Spec Wizard tab) to generate objectives/tech stack/features/architecture/quality.
3) Generate plan: call planning endpoints (capacity plan) or use Planning tab to inspect.
4) Run task pipeline job (Jobs tab: "Run task pipeline for sprint").
5) Check ready-for-dev tasks + Sprint Task Board.
6) Observability:
   - System status: `GET /status/overview`
   - Project diagnostics: `GET /projects/{id}/diagnostics`
   - Metrics: `GET /metrics`
   - Logs: JSON formatted on stdout (request_id/project_id/job_id context).

## Tests
```
pytest
```

## Notes
- Default LLM provider is `dummy`; configure real provider via env in `.env`.
- CORS is open for local dev; tighten for prod.
- Auth is not included; intended for internal/dev use.
