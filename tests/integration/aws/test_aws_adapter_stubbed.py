from __future__ import annotations

import asyncio

import pytest

from src.adapters.telemetry.factory import get_telemetry_collectors
from src.agent_runtime.settings import clear_agent_runtime_settings_cache
from src.config import clear_app_settings_cache


def test_aws_telemetry_adapter_reports_missing_log_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEMETRY_ADAPTER", "aws")
    monkeypatch.delenv("AWS_LOG_GROUP", raising=False)
    clear_agent_runtime_settings_cache()
    clear_app_settings_cache()

    result = asyncio.run(get_telemetry_collectors().query_logs("checkout-service", "checkout-service"))

    assert "aws-cloudwatch-logs" in result
    assert "not_configured" in result
