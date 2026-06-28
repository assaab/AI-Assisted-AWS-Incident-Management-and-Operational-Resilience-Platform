from __future__ import annotations

from typing import Any

import httpx

from src.config import get_app_settings


class CheckoutServiceClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or get_app_settings().checkout_service_url).rstrip("/")

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            assert isinstance(data, dict)
            return data

    async def metrics(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/metrics/business")
            response.raise_for_status()
            data = response.json()
            assert isinstance(data, dict)
            return data

    async def inject_deployment_failure(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self.base_url}/faults/deployment-regression")
            response.raise_for_status()
            data = response.json()
            assert isinstance(data, dict)
            return data

    async def rollback(self, to_revision: str = "checkout-r42") -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.base_url}/deployments/rollback", json={"to_revision": to_revision})
            response.raise_for_status()
            data = response.json()
            assert isinstance(data, dict)
            return data

    async def restart(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.base_url}/operations/restart")
            response.raise_for_status()
            data = response.json()
            assert isinstance(data, dict)
            return data

    async def scale(self, replicas: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{self.base_url}/operations/scale", json={"replicas": replicas})
            response.raise_for_status()
            data = response.json()
            assert isinstance(data, dict)
            return data

    async def verify_recovery(self) -> tuple[bool, dict[str, Any]]:
        metrics = await self.metrics()
        error_rate = float(metrics.get("error_rate_percent", 100.0))
        latency = float(metrics.get("p95_latency_ms", 9999.0))
        healthy = bool(metrics.get("healthy", False))
        return healthy and error_rate < 1.0 and latency < 300.0, metrics
