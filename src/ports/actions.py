from __future__ import annotations

from typing import Protocol

from src.domain.contracts.models import ActionRequest, ActionResult


class ActionPort(Protocol):
    async def execute(self, action: ActionRequest) -> ActionResult:
        """Execute or dry-run a controlled operational action."""
