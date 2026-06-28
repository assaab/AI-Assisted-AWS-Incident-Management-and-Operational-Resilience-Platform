from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.agent_runtime.settings import get_agent_runtime_settings


@runtime_checkable
class ChangeFeedProtocol(Protocol):
    async def get_recent_deployments(self, service: str) -> str: ...


class StubChangeFeedClient:
    async def get_recent_deployments(self, service: str) -> str:
        if service == "checkout-service":
            return (
                "Deployment checkout-r43 applied to checkout-service 12 minutes before alert; "
                "previous stable revision checkout-r42"
            )
        return f"Deployment v2026.03.19 applied to {service} 12 minutes before alert"


def get_change_feed_client() -> ChangeFeedProtocol:
    s = get_agent_runtime_settings()
    if s.change_feed_adapter == "aws":
        from src.adapters.aws.change_feed import AwsEcsChangeFeedClient

        return AwsEcsChangeFeedClient()
    if s.change_feed_adapter == "stub":
        return StubChangeFeedClient()
    return StubChangeFeedClient()


# Legacy name
ChangeFeedClient = StubChangeFeedClient
