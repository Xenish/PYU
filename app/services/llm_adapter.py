import asyncio
import json
import random
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import LLMIntent
from app.services.llm_logs import log_llm_call
from app.services.llm_policy import (
    LLMJobBudgetExceeded,
    LLMQuotaExceeded,
    backoff_sleep,
    check_and_increment_project_quota,
    check_job_budget,
)
from app.observability import metrics
from app.observability.logging import get_logger


class LLMError(Exception):
    """LLM çağrısı veya validasyon hatası."""


async def _raw_llm_call(prompt: str, *, provider: str, model: str, temperature: float | None, max_tokens: int | None) -> str:
    """
    Tek noktadan ham LLM çağrısı. Şimdilik dummy provider destekleniyor.
    Gerçek provider eklendiğinde sadece bu fonksiyon genişletilir.
    """
    if provider == "dummy":
        # Deterministic dummy output for tests/dev
        return json.dumps(
            {
                "objectives": [
                    {"title": "Dummy Hedef", "description": "Açıklama", "priority": 1}
                ]
            }
        )
    if provider == "openai":
        try:
            import openai  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise LLMError("openai paketi yüklü değil. pip install openai ile kurun.") from exc

        client = openai.OpenAI()
        completion = client.chat.completions.create(  # type: ignore[attr-defined]
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generator. Always return strictly valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content or ""
        if not content.strip():
            raise LLMError("LLM boş içerik döndürdü.")
        return content
    raise LLMError(f"Provider '{provider}' desteklenmiyor")


async def call_llm(
    prompt: str,
    response_model: type[BaseModel],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    db: AsyncSession | None = None,
    project_id: int | None = None,
    step_type: str | None = None,
    job_id: int | None = None,
    intent: LLMIntent | None = None,
) -> BaseModel:
    """
    Tek LLM entrypoint'i.
    - prompt string alır
    - policy: quota + budget + retry/backoff
    - raw LLM çağrısı yapar
    - JSON parse eder
    - Pydantic response_model ile validate eder
    - Valid değilse LLMError fırlatır
    """
    settings = get_settings()
    provider = settings.llm_provider
    model = settings.llm_model
    temp = temperature if temperature is not None else settings.llm_temperature
    tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens

    attempts = settings.llm_max_retries + 1
    last_err: Exception | None = None

    if intent and project_id is None:
        raise LLMError("project_id is required when intent is provided for quota tracking")

    for attempt in range(attempts):
        try:
            if db and project_id is not None:
                await check_and_increment_project_quota(
                    db,
                    project_id,
                    max_calls=settings.llm_project_daily_max_calls,
                )
            check_job_budget(job_id, settings.llm_job_max_calls)

            raw = await _raw_llm_call(
                prompt, provider=provider, model=model, temperature=temp, max_tokens=tokens
            )
            if not raw or not str(raw).strip():
                raise LLMError("LLM yanıtı boş geldi; parse edilemedi.")

            # Try to parse JSON
            try:
                data: Any = json.loads(raw)
            except json.JSONDecodeError as err:
                # Try to extract JSON from markdown code blocks or surrounding text
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', raw, re.DOTALL)
                if not json_match:
                    # Try to find raw JSON object
                    json_match = re.search(r'(\{[^{}]*\{.*\}[^{}]*\})', raw, re.DOTALL)

                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        pass

                if 'data' not in locals():
                    # Log the raw response for debugging
                    get_logger("masper.llm", component="llm").error(
                        "llm.json_parse_error",
                        extra={
                            "intent": intent.value if intent else None,
                            "error": str(err),
                            "raw_response": raw[:500],  # First 500 chars
                        }
                    )
                    raise LLMError(f"LLM yanıtı JSON parse edilemedi: {err}") from err
            validated = response_model.model_validate(data)
            if db and step_type:
                await log_llm_call(
                    db,
                    project_id=project_id,
                    step_type=step_type,
                    status="success",
                    request_payload=prompt,
                    response_payload=validated.model_dump(),
                )
            metrics.llm_calls_total.labels(intent=intent.value if intent else "unknown", outcome="success").inc()
            get_logger("masper.llm", component="llm").info(
                "llm.success",
                extra={
                    "intent": intent.value if intent else None,
                    "project_id": project_id,
                    "job_id": job_id,
                },
            )
            return validated
        except (LLMQuotaExceeded, LLMJobBudgetExceeded):
            if db and step_type:
                await log_llm_call(
                    db,
                    project_id=project_id,
                    step_type=step_type,
                    status="fail",
                    request_payload=prompt,
                    response_payload={"error": "quota_or_budget_exceeded"},
                )
            metrics.llm_calls_total.labels(intent=intent.value if intent else "unknown", outcome="quota_or_budget").inc()
            raise
        except (json.JSONDecodeError, ValidationError, LLMError) as exc:
            last_err = exc
        except Exception as exc:  # noqa: BLE001
            last_err = exc

        if attempt < attempts - 1:
            await backoff_sleep(
                attempt=attempt,
                initial=settings.llm_initial_backoff_seconds,
                maximum=settings.llm_max_backoff_seconds,
            )
        else:
            break

    if db and step_type:
        await log_llm_call(
            db,
            project_id=project_id,
            step_type=step_type,
            status="fail",
            request_payload=prompt,
            response_payload={"error": str(last_err) if last_err else "unknown"},
        )
    metrics.llm_calls_total.labels(intent=intent.value if intent else "unknown", outcome="fail").inc()
    get_logger("masper.llm", component="llm").error(
        "llm.failed",
        extra={
            "intent": intent.value if intent else None,
            "project_id": project_id,
            "job_id": job_id,
            "error": str(last_err),
        },
    )
    raise LLMError(f"LLM çağrısı başarısız: {last_err}") from last_err
