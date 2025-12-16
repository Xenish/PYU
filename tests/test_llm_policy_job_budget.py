import pytest

from app.services.llm_policy import LLMJobBudgetExceeded, check_job_budget


def test_job_budget_enforced():
    job_id = 123
    for _ in range(3):
        check_job_budget(job_id, max_calls=3)
    with pytest.raises(LLMJobBudgetExceeded):
        check_job_budget(job_id, max_calls=3)
