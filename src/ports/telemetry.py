from __future__ import annotations

from typing import Protocol


class TelemetryPort(Protocol):
    async def collect(self, incident_id: str) -> list[dict[str, object]]:
        """Collect telemetry evidence for an incident."""
