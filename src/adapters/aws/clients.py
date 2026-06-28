from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import get_app_settings


@dataclass(frozen=True)
class AwsRetryClassification:
    retryable: bool
    reason: str


def classify_aws_error(exc: Exception) -> AwsRetryClassification:
    code = exc.__class__.__name__
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        error = response.get("Error")
        if isinstance(error, dict):
            raw_code = error.get("Code")
            if isinstance(raw_code, str):
                code = raw_code
    retryable_codes = {
        "ThrottlingException",
        "Throttling",
        "TooManyRequestsException",
        "RequestTimeout",
        "RequestTimeoutException",
        "ServiceUnavailableException",
        "InternalException",
        "InternalServerError",
    }
    terminal_codes = {
        "AccessDeniedException",
        "AccessDenied",
        "UnauthorizedOperation",
        "ValidationException",
        "InvalidParameterException",
        "ResourceNotFoundException",
        "ClusterNotFoundException",
        "ServiceNotFoundException",
    }
    if code in retryable_codes:
        return AwsRetryClassification(True, code)
    if code in terminal_codes:
        return AwsRetryClassification(False, code)
    return AwsRetryClassification(False, code)


class AwsClientFactory:
    def __init__(self, clients: dict[str, Any] | None = None) -> None:
        self._clients = clients or {}

    def client(self, service_name: str) -> Any:
        if service_name in self._clients:
            return self._clients[service_name]
        settings = get_app_settings()
        import boto3

        kwargs: dict[str, str] = {"region_name": settings.aws_region}
        if settings.aws_profile:
            kwargs["profile_name"] = settings.aws_profile
        session = boto3.Session(**kwargs)
        client = session.client(service_name)
        self._clients[service_name] = client
        return client
