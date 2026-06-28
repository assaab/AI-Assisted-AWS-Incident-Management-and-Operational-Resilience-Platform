from __future__ import annotations

from typing import Any, cast

from src.adapters.actions.typed_adapters import AdapterResult
from src.adapters.aws.clients import AwsClientFactory, classify_aws_error
from src.config import get_app_settings
from src.domain.contracts.models import ActionRequest, ActionType


class AwsEcsActionAdapter:
    def __init__(self, factory: AwsClientFactory | None = None) -> None:
        self._factory = factory or AwsClientFactory()

    def capabilities(self) -> dict[str, object]:
        return {
            "mode": "aws",
            "provider": "aws-ecs",
            "supported_actions": [
                ActionType.RESTART_SERVICE.value,
                ActionType.ROLLBACK_DEPLOYMENT.value,
                ActionType.SCALE_WORKLOAD.value,
            ],
            "dry_run_default": True,
        }

    async def verify(self, action: ActionRequest) -> tuple[bool, dict[str, Any]]:
        settings = get_app_settings()
        if not settings.aws_ecs_cluster or not settings.aws_ecs_service:
            return False, {"status": "not_configured"}
        response = self._factory.client("ecs").describe_services(
            cluster=settings.aws_ecs_cluster,
            services=[settings.aws_ecs_service],
        )
        services = response.get("services", [])
        service = services[0] if services else {}
        rollout_state = ""
        deployments = service.get("deployments", [])
        if deployments:
            rollout_state = str(deployments[0].get("rolloutState", ""))
        desired = int(service.get("desiredCount", 0))
        running = int(service.get("runningCount", 0))
        if action.action_type == ActionType.SCALE_WORKLOAD:
            expected = int(action.parameters.get("maxReplicas", action.parameters.get("replicas", desired)))
            ok = desired == expected
        else:
            ok = running >= 1 and rollout_state in {"COMPLETED", ""}
        return ok, {
            "provider": "aws-ecs",
            "cluster": settings.aws_ecs_cluster,
            "service": settings.aws_ecs_service,
            "desired_count": desired,
            "running_count": running,
            "rollout_state": rollout_state,
        }

    async def run(self, action: ActionRequest) -> AdapterResult:
        settings = get_app_settings()
        cluster = settings.aws_ecs_cluster
        service = settings.aws_ecs_service or action.target
        if not cluster or not service:
            return AdapterResult(False, "AWS ECS adapter is not configured", {"missing": ["AWS_ECS_CLUSTER"]})
        planned = self._planned_operation(action, cluster, service)
        if action.dry_run or settings.aws_action_dry_run:
            return AdapterResult(
                True,
                f"AWS dry-run planned for {action.action_type.value}",
                {
                    "provider": "aws-ecs",
                    "dry_run": True,
                    "operation": planned,
                    "verification": "describe_services after update",
                    "retry_classification": "not_applicable",
                },
            )
        try:
            response = self._execute(action, cluster, service)
            verified, verification = await self.verify(action)
            return AdapterResult(
                verified,
                f"AWS ECS {action.action_type.value} {'verified' if verified else 'completed but not verified'}",
                {
                    "provider": "aws-ecs",
                    "dry_run": False,
                    "operation": planned,
                    "response": response,
                    "verification": verification,
                },
            )
        except Exception as exc:
            classification = classify_aws_error(exc)
            return AdapterResult(
                False,
                f"AWS ECS action failed: {classification.reason}",
                {
                    "provider": "aws-ecs",
                    "dry_run": False,
                    "operation": planned,
                    "error": str(exc),
                    "retryable": classification.retryable,
                    "retry_classification": classification.reason,
                },
            )

    def _planned_operation(self, action: ActionRequest, cluster: str, service: str) -> dict[str, object]:
        if action.action_type == ActionType.RESTART_SERVICE:
            return {"api": "ecs.update_service", "cluster": cluster, "service": service, "forceNewDeployment": True}
        if action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
            task_definition = str(action.parameters.get("to_revision", action.parameters.get("taskDefinition", "")))
            return {
                "api": "ecs.update_service",
                "cluster": cluster,
                "service": service,
                "taskDefinition": task_definition,
            }
        if action.action_type == ActionType.SCALE_WORKLOAD:
            desired = int(action.parameters.get("maxReplicas", action.parameters.get("replicas", 1)))
            return {"api": "ecs.update_service", "cluster": cluster, "service": service, "desiredCount": desired}
        return {"api": "unsupported", "cluster": cluster, "service": service}

    def _execute(self, action: ActionRequest, cluster: str, service: str) -> dict[str, Any]:
        ecs = self._factory.client("ecs")
        if action.action_type == ActionType.RESTART_SERVICE:
            return cast(dict[str, Any], ecs.update_service(cluster=cluster, service=service, forceNewDeployment=True))
        if action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
            task_definition = str(action.parameters.get("to_revision", action.parameters.get("taskDefinition", "")))
            return cast(
                dict[str, Any],
                ecs.update_service(cluster=cluster, service=service, taskDefinition=task_definition),
            )
        if action.action_type == ActionType.SCALE_WORKLOAD:
            desired = int(action.parameters.get("maxReplicas", action.parameters.get("replicas", 1)))
            return cast(dict[str, Any], ecs.update_service(cluster=cluster, service=service, desiredCount=desired))
        raise ValueError(f"Unsupported AWS ECS action {action.action_type.value}")
