from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Sprint Planner"
    env: str = "local"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./app.db"
    log_level: str = "info"
    llm_provider: str = "dummy"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: str | None = None
    llm_temperature: float = 0.2
    llm_max_tokens: int | None = None
    llm_max_retries: int = 2
    llm_initial_backoff_seconds: float = 0.3
    llm_max_backoff_seconds: float = 3.0
    llm_job_max_calls: int = 50
    llm_project_daily_max_calls: int = 500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    # Cached settings to avoid re-parsing env on each dependency call
    return Settings()
