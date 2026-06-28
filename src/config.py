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
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_profile: str = Field(default="", alias="AWS_PROFILE")
    aws_ecs_cluster: str = Field(default="", alias="AWS_ECS_CLUSTER")
    aws_ecs_service: str = Field(default="", alias="AWS_ECS_SERVICE")
    aws_log_group: str = Field(default="", alias="AWS_LOG_GROUP")
    aws_metric_namespace: str = Field(default="AWS/ECS", alias="AWS_METRIC_NAMESPACE")
    aws_deployment_lookback_minutes: int = Field(default=60, alias="AWS_DEPLOYMENT_LOOKBACK_MINUTES")
    aws_action_dry_run: bool = Field(default=True, alias="AWS_ACTION_DRY_RUN")


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


def clear_app_settings_cache() -> None:
    get_app_settings.cache_clear()
