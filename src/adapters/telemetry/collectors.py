"""Backward-compatible exports for telemetry collectors."""

from __future__ import annotations

from src.adapters.telemetry.factory import get_telemetry_collectors
from src.adapters.telemetry.stub import StubTelemetryCollectors

# Legacy class name used by imports
TelemetryCollectors = StubTelemetryCollectors

__all__ = ["TelemetryCollectors", "StubTelemetryCollectors", "get_telemetry_collectors"]
