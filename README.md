# AI Sprint Planner (Skeleton)

## Geliştirme

- Bağımlılıklar: `pip install -r requirements.txt`
- Çalıştır: `uvicorn main:app --reload`
- Sağlık kontrolü: `GET /health` (DB check) veya `GET /health/ping`
- Migration: `alembic upgrade head`
- Test: `pytest`
- Frontend: `cd frontend && npm install && npm run dev` (Next.js app at http://localhost:3000)
- Observability: JSON log/metrics/status endpoint detayları için `docs/observability.md`
- V1: Kurulum ve kapsam için `docs/GETTING_STARTED.md` ve `docs/V1_RELEASE.md` dosyalarına bakın.

## Notlar

- Async stack (FastAPI + SQLAlchemy async) kullanılıyor.
- Config tek kaynaktan (`app/core/config.py`) okunuyor.
- Soft delete için query helper'ı kullan (`only_active`); gerekirse `execution_options(include_deleted=True)` ile dahil edebilirsin.
- LLM adapter tek entrypoint: `app/services/llm_adapter.call_llm`. Varsayılan provider `dummy`; `.env` ile özelleştir:
  - `LLM_PROVIDER=dummy`
  - `LLM_MODEL=gpt-4.1-mini`
  - `LLM_API_KEY=...`

## Planning Modes

| Endpoint | Amaç |
| --- | --- |
| `POST /projects/{id}/planning/generate-sprint-plan` | Basit skeleton plan (SP/capacity yok) |
| `POST /projects/{id}/planning/generate-capacity-plan` | SP + capacity-aware plan (backlog/quality_summary içerir) |

### Epic Generation - Destructive Behavior

`POST /projects/{id}/planning/generate-epics` çağrısı **destructive** bir operasyondur:
- İlgili proje için mevcut **Epic** ve **EpicDependency** kayıtlarını temizler.
- Spec'ten epikleri **yeniden üretir**.

Eğer epiklere manuel düzenleme yaptıysanız (title/description/priority vb.), bu çağrı sonrası kaybolur. V1 davranışı "clear & regenerate"tir; merge stratejisi ileride ele alınacaktır.
