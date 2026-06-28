from __future__ import annotations

import asyncio
import random
from typing import Final

from apps.api.routers.audit.store import audit_store
from src.adapters.actions.typed_adapters import TypedActionAdapterRegistry
from src.agent_runtime.sandbox import is_privileged_action, log_nemoclaw_style_sandbox
from src.agent_runtime.settings import get_agent_runtime_settings
from src.domain.contracts.models import ActionRequest
from src.observability.logging import get_logger
from src.persistence.idempotency import idempotency_store
from src.security.context import SecurityContext


class ActionExecutor:
    def __init__(self) -> None:
        self._logger = get_logger("action-executor")
        self.registry = TypedActionAdapterRegistry()
        self._default_retry_limit: Final[int] = 3

    async def _run_with_retries(self, action: ActionRequest, context: SecurityContext) -> tuple[bool, str]:
        attempts = 0
        while attempts < self._default_retry_limit:
            attempts += 1
            try:
                result = await asyncio.wait_for(
                    self.registry.run(action, context),
                    timeout=action.timeout_seconds,
                )
                if result.success:
                    return True, result.message
                if attempts >= self._default_retry_limit:
                    return False, result.message
            except TimeoutError:
                if attempts >= self._default_retry_limit:
                    return False, f"Action timed out after {attempts} attempts"
            await asyncio.sleep(0.2 + random.uniform(0.0, 0.2))
        return False, "Action failed after retries"

    async def execute(self, action: ActionRequest) -> tuple[bool, str]:
        if not await idempotency_store.claim(action.idempotency_key, action.action_id):
            return True, f"Skipped duplicate idempotency key {action.idempotency_key}"

        if get_agent_runtime_settings().sandbox_enabled and is_privileged_action(action):
            log_nemoclaw_style_sandbox(action)

        context = SecurityContext(
            agent_identity="execution-agent",
            tool_identity=f"adapter:{action.action_type.value}",
            allowed_targets=[action.target, "k8s-*", "arc-*"],
        )
        success, message = await self._run_with_retries(action, context)
        await audit_store.append(
            "adapter_execution",
            {
                "action_id": action.action_id,
                "action_type": action.action_type.value,
                "target": action.target,
                "idempotency_key": action.idempotency_key,
                "dry_run": action.dry_run,
                "success": success,
                "message": message,
            },
        )
        self._logger.info("adapter_execution_complete", action_id=action.action_id, success=success)
        return success, message
