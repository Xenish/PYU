from datetime import date

from app.core.config import get_settings
from app.models.llm_usage import LLMUsage


def test_llm_usage_model_fields():
    usage = LLMUsage(project_id=1, date=date.today(), call_count=2)
    assert usage.call_count == 2


def test_llm_policy_defaults():
    settings = get_settings()
    assert settings.llm_max_retries >= 0
    assert settings.llm_project_daily_max_calls > 0
