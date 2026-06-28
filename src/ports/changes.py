from __future__ import annotations

from typing import Protocol


class ChangePort(Protocol):
    async def recent_changes(self, service: str) -> list[dict[str, object]]:
        """Return recent deployment or configuration changes for a service."""
