from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.adapters.local.checkout_client import CheckoutServiceClient
from src.config import get_app_settings
from src.domain.contracts.models import ActionRequest, ActionType
from src.security.context import SecurityContext


@dataclass
class AdapterResult:
    success: bool
    message: str
    details: dict[str, Any]


class RestartServiceParams(BaseModel):
    service: str = Field(min_length=1)


class ScaleWorkloadParams(BaseModel):
    service: str = Field(min_length=1)
    maxReplicas: int = Field(ge=1, le=20)


class RollbackDeploymentParams(BaseModel):
    deployment: str = Field(min_length=1)
    to_revision: str = Field(min_length=1)


class TypedActionAdapterRegistry:
    def __init__(self) -> None:
        self.supported_actions = {
            ActionType.QUERY_METRICS,
            ActionType.QUERY_LOGS,
            ActionType.GET_RECENT_DEPLOYMENTS,
            ActionType.GET_TOPOLOGY,
            ActionType.RESTART_SERVICE,
            ActionType.SCALE_WORKLOAD,
            ActionType.ROLLBACK_DEPLOYMENT,
            ActionType.DRAIN_NODE,
            ActionType.OPEN_TICKET,
            ActionType.PAGE_HUMAN,
            ActionType.RUN_ANSIBLE_JOB,
        }
        self.local_client = CheckoutServiceClient()

    def capabilities(self) -> dict[str, object]:
        settings = get_app_settings()
        executable = {ActionType.RESTART_SERVICE, ActionType.SCALE_WORKLOAD, ActionType.ROLLBACK_DEPLOYMENT}
        return {
            "mode": settings.execution_mode,
            "dry_run_default": settings.execute_action_dry_run,
            "supported_actions": sorted(action.value for action in self.supported_actions),
            "executable_actions": sorted(
                action.value for action in executable if settings.execution_mode in {"local", "aws"}
            ),
        }

    def _validate_parameters(self, action: ActionRequest) -> None:
        if action.action_type == ActionType.RESTART_SERVICE:
            RestartServiceParams.model_validate(action.parameters)
        elif action.action_type == ActionType.SCALE_WORKLOAD:
            ScaleWorkloadParams.model_validate(action.parameters)
        elif action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
            RollbackDeploymentParams.model_validate(action.parameters)

    async def run(self, action: ActionRequest, context: SecurityContext) -> AdapterResult:
        if action.action_type not in self.supported_actions:
            return AdapterResult(False, f"Unsupported action type {action.action_type}", {})
        if not context.can_access_target(action.target):
            return AdapterResult(False, f"Target {action.target} is not allowlisted", {})
        try:
            self._validate_parameters(action)
        except ValidationError as exc:
            return AdapterResult(False, "Action parameters failed validation", {"errors": exc.errors()})
        settings = get_app_settings()
        if settings.execution_mode == "aws":
            from src.adapters.aws.actions import AwsEcsActionAdapter

            if action.action_type in {
                ActionType.RESTART_SERVICE,
                ActionType.SCALE_WORKLOAD,
                ActionType.ROLLBACK_DEPLOYMENT,
            }:
                return await AwsEcsActionAdapter().run(action)
        if action.dry_run:
            return AdapterResult(True, f"Dry-run completed for {action.action_type.value}", {"dry_run": True})
        if settings.execution_mode != "local":
            return AdapterResult(
                False,
                f"No executable adapter configured for mode {settings.execution_mode}",
                {"dry_run": False, "capabilities": self.capabilities()},
            )
        if action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
            revision = str(action.parameters.get("to_revision", "checkout-r42"))
            result = await self.local_client.rollback(revision)
            return AdapterResult(True, "Rolled back checkout deployment", {"dry_run": False, "workload": result})
        if action.action_type == ActionType.RESTART_SERVICE:
            result = await self.local_client.restart()
            return AdapterResult(True, "Restarted checkout service", {"dry_run": False, "workload": result})
        if action.action_type == ActionType.SCALE_WORKLOAD:
            replicas = int(action.parameters.get("maxReplicas", action.parameters.get("replicas", 3)))
            result = await self.local_client.scale(replicas)
            return AdapterResult(True, "Scaled checkout service", {"dry_run": False, "workload": result})
        return AdapterResult(
            False,
            f"Action {action.action_type.value} is read-only or unsupported for execution",
            {"dry_run": False, "capabilities": self.capabilities()},
        )
