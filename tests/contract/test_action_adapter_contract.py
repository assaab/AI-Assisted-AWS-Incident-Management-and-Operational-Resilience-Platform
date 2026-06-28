from __future__ import annotations

import asyncio

import pytest

from src.adapters.actions.typed_adapters import TypedActionAdapterRegistry
from src.config import clear_app_settings_cache
from src.domain.contracts.models import ActionRequest, ActionType
from src.security.context import SecurityContext


def test_action_adapter_contract_supports_aws_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXECUTION_MODE", "aws")
    monkeypatch.setenv("AWS_ECS_CLUSTER", "checkout-cluster")
    monkeypatch.setenv("AWS_ECS_SERVICE", "checkout-service")
    clear_app_settings_cache()

    action = ActionRequest(
        action_id="act_contract",
        action_type=ActionType.ROLLBACK_DEPLOYMENT,
        target="checkout-service",
        parameters={"deployment": "checkout-service", "to_revision": "checkout-r42"},
        idempotency_key="idem_contract",
        dry_run=True,
    )
    result = asyncio.run(
        TypedActionAdapterRegistry().run(
            action,
            SecurityContext(
                agent_identity="test",
                tool_identity="adapter:test",
                allowed_targets=["checkout-service"],
            ),
        ),
    )

    assert result.success is True
    assert result.details["provider"] == "aws-ecs"
    assert result.details["dry_run"] is True
