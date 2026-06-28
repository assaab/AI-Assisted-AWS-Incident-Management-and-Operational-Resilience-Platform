from __future__ import annotations

import json
from typing import Any

from src.adapters.aws.clients import AwsClientFactory, classify_aws_error
from src.config import get_app_settings


class AwsEcsChangeFeedClient:
    def __init__(self, factory: AwsClientFactory | None = None) -> None:
        self._factory = factory or AwsClientFactory()

    async def get_recent_deployments(self, service: str) -> str:
        settings = get_app_settings()
        cluster = settings.aws_ecs_cluster
        ecs_service = settings.aws_ecs_service or service
        if not cluster or not ecs_service:
            return json.dumps(
                {
                    "provider": "aws-ecs",
                    "service": service,
                    "status": "not_configured",
                    "missing": ["AWS_ECS_CLUSTER", "AWS_ECS_SERVICE"],
                },
                sort_keys=True,
            )
        try:
            response = self._factory.client("ecs").describe_services(cluster=cluster, services=[ecs_service])
            deployments = response.get("services", [{}])[0].get("deployments", [])
            payload: dict[str, Any] = {
                "provider": "aws-ecs",
                "cluster": cluster,
                "service": ecs_service,
                "deployments": [
                    {
                        "id": item.get("id"),
                        "status": item.get("status"),
                        "task_definition": item.get("taskDefinition"),
                        "rollout_state": item.get("rolloutState"),
                        "created_at": item.get("createdAt"),
                        "updated_at": item.get("updatedAt"),
                        "desired_count": item.get("desiredCount"),
                        "running_count": item.get("runningCount"),
                    }
                    for item in deployments
                ],
            }
        except Exception as exc:
            classification = classify_aws_error(exc)
            payload = {
                "provider": "aws-ecs",
                "cluster": cluster,
                "service": ecs_service,
                "error": str(exc),
                "retryable": classification.retryable,
                "classification": classification.reason,
            }
        return json.dumps(payload, default=str, sort_keys=True)
