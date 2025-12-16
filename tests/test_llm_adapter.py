import pytest
from pydantic import BaseModel

from app.services import llm_adapter


class DemoResponse(BaseModel):
    foo: str


@pytest.mark.asyncio
async def test_llm_adapter_happy_path(monkeypatch):
    async def fake_raw(prompt: str, provider: str, model: str, temperature: float | None, max_tokens: int | None):
        return '{"foo":"bar"}'

    monkeypatch.setattr(llm_adapter, "_raw_llm_call", fake_raw)
    resp = await llm_adapter.call_llm("test", DemoResponse)
    assert resp.foo == "bar"


@pytest.mark.asyncio
async def test_llm_adapter_invalid_json(monkeypatch):
    async def fake_raw(prompt: str, provider: str, model: str, temperature: float | None, max_tokens: int | None):
        return '{"foo": }'

    monkeypatch.setattr(llm_adapter, "_raw_llm_call", fake_raw)
    with pytest.raises(llm_adapter.LLMError):
        await llm_adapter.call_llm("test", DemoResponse)
