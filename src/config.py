from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    execution_mode: str = Field(default="local", alias="EXECUTION_MODE")
    execute_action_dry_run: bool = Field(default=True, alias="EXECUTE_ACTION_DRY_RUN")
    auth_mode: str = Field(default="demo", alias="AUTH_MODE")
    checkout_service_url: str = Field(default="http://localhost:8090", alias="CHECKOUT_SERVICE_URL")
    postgres_dsn: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/sre_agent",
        alias="POSTGRES_DSN",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


def clear_app_settings_cache() -> None:
    get_app_settings.cache_clear()
