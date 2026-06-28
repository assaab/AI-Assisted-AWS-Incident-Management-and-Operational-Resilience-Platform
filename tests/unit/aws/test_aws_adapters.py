from __future__ import annotations

import asyncio

import pytest

from src.config import clear_app_settings_cache
from src.domain.contracts.models import ActionRequest, ActionType


def _action(action_type: ActionType, parameters: dict[str, object] | None = None) -> ActionRequest:
    return ActionRequest(
        action_id="act_test",
        action_type=action_type,
        target="checkout-service",
        parameters=parameters or {},
        idempotency_key="idem_test",
        dry_run=True,
        timeout_seconds=10,
    )


def test_aws_action_adapter_dry_run_does_not_require_boto3(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.adapters.aws.actions import AwsEcsActionAdapter

    monkeypatch.setenv("AWS_ECS_CLUSTER", "checkout-cluster")
    monkeypatch.setenv("AWS_ECS_SERVICE", "checkout-service")
    clear_app_settings_cache()

    result = asyncio.run(AwsEcsActionAdapter().run(_action(ActionType.RESTART_SERVICE)))

    assert result.success is True
    assert result.details["dry_run"] is True
    assert result.details["operation"]["api"] == "ecs.update_service"


def test_aws_ecs_scale_executes_with_stubber(monkeypatch: pytest.MonkeyPatch) -> None:
    boto3 = pytest.importorskip("boto3")
    botocore_stub = pytest.importorskip("botocore.stub")
    from src.adapters.aws.actions import AwsEcsActionAdapter
    from src.adapters.aws.clients import AwsClientFactory

    monkeypatch.setenv("AWS_ECS_CLUSTER", "checkout-cluster")
    monkeypatch.setenv("AWS_ECS_SERVICE", "checkout-service")
    monkeypatch.setenv("AWS_ACTION_DRY_RUN", "false")
    clear_app_settings_cache()

    ecs = boto3.client(
        "ecs",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        aws_session_token="test",
    )
    stubber = botocore_stub.Stubber(ecs)
    stubber.add_response(
        "update_service",
        {"service": {"serviceName": "checkout-service", "desiredCount": 3, "runningCount": 2}},
        {"cluster": "checkout-cluster", "service": "checkout-service", "desiredCount": 3},
    )
    stubber.add_response(
        "describe_services",
        {"services": [{"serviceName": "checkout-service", "desiredCount": 3, "runningCount": 2, "deployments": []}]},
        {"cluster": "checkout-cluster", "services": ["checkout-service"]},
    )
    with stubber:
        adapter = AwsEcsActionAdapter(AwsClientFactory({"ecs": ecs}))
        result = asyncio.run(
            adapter.run(_action(ActionType.SCALE_WORKLOAD, {"maxReplicas": 3}).model_copy(update={"dry_run": False}))
        )

    assert result.success is True
    assert result.details["verification"]["desired_count"] == 3
