import pytest

from pydantic import BaseModel

from app.services import llm_adapter


class DemoResponse(BaseModel):
    ok: str


@pytest.mark.asyncio
async def test_llm_adapter_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}

    async def fake_raw(prompt, provider, model, temperature, max_tokens):
        calls["count"] += 1
        if calls["count"] < 3:
            raise llm_adapter.LLMError("transient")
        return '{"ok": "yes"}'

    monkeypatch.setattr(llm_adapter, "_raw_llm_call", fake_raw)
    resp = await llm_adapter.call_llm("prompt", DemoResponse, db=None, project_id=None, step_type=None)
    assert resp.ok == "yes"
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_llm_adapter_gives_up_after_retries(monkeypatch):
    async def fake_raw(prompt, provider, model, temperature, max_tokens):
        raise llm_adapter.LLMError("always fail")

    monkeypatch.setattr(llm_adapter, "_raw_llm_call", fake_raw)
    with pytest.raises(llm_adapter.LLMError):
        await llm_adapter.call_llm("prompt", DemoResponse, db=None, project_id=None, step_type=None)
