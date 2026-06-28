from __future__ import annotations

import json

from src.adapters.local.checkout_client import CheckoutServiceClient


class LocalCheckoutTelemetryCollectors:
    async def query_metrics(self, service: str, resource: str) -> str:
        if service != "checkout-service":
            return json.dumps({"service": service, "resource": resource, "status": "no-local-workload"})
        return json.dumps(await CheckoutServiceClient().metrics(), sort_keys=True)

    async def query_logs(self, service: str, resource: str) -> str:
        if service != "checkout-service":
            return json.dumps({"service": service, "resource": resource, "log_pattern": "none"})
        metrics = await CheckoutServiceClient().metrics()
        pattern = "payment_timeout_spike" if float(metrics.get("error_rate_percent", 0)) > 1 else "normal_checkout"
        return json.dumps(
            {
                "service": service,
                "resource": resource,
                "log_pattern": pattern,
                "revision": metrics.get("revision"),
                "window_minutes": 5,
            },
            sort_keys=True,
        )

    async def query_topology(self, service: str, resource: str) -> str:
        return json.dumps(
            {
                "service": service,
                "resource": resource,
                "dependencies": ["payments-api", "inventory-api", "orders-db"],
            },
            sort_keys=True,
        )
