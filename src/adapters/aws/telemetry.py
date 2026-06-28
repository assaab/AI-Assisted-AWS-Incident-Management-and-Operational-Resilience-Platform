from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from src.adapters.aws.clients import AwsClientFactory, classify_aws_error
from src.config import get_app_settings


class AwsCloudWatchTelemetryCollectors:
    def __init__(self, factory: AwsClientFactory | None = None) -> None:
        self._factory = factory or AwsClientFactory()

    async def query_metrics(self, service: str, resource: str) -> str:
        settings = get_app_settings()
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=settings.aws_deployment_lookback_minutes)
        query = {
            "Id": "checkout_error_rate",
            "MetricStat": {
                "Metric": {
                    "Namespace": settings.aws_metric_namespace,
                    "MetricName": "HTTPCode_Target_5XX_Count",
                    "Dimensions": [
                        {"Name": "ServiceName", "Value": settings.aws_ecs_service or service},
                        {"Name": "ClusterName", "Value": settings.aws_ecs_cluster or resource},
                    ],
                },
                "Period": 60,
                "Stat": "Sum",
            },
            "ReturnData": True,
        }
        try:
            response = self._factory.client("cloudwatch").get_metric_data(
                MetricDataQueries=[query],
                StartTime=start,
                EndTime=end,
            )
            payload: dict[str, Any] = {
                "provider": "aws-cloudwatch",
                "service": service,
                "resource": resource,
                "metric_namespace": settings.aws_metric_namespace,
                "window_minutes": settings.aws_deployment_lookback_minutes,
                "result": response.get("MetricDataResults", []),
            }
        except Exception as exc:
            classification = classify_aws_error(exc)
            payload = {
                "provider": "aws-cloudwatch",
                "service": service,
                "resource": resource,
                "error": str(exc),
                "retryable": classification.retryable,
                "classification": classification.reason,
            }
        return json.dumps(payload, default=str, sort_keys=True)

    async def query_logs(self, service: str, resource: str) -> str:
        settings = get_app_settings()
        end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_ms = end_ms - settings.aws_deployment_lookback_minutes * 60 * 1000
        if not settings.aws_log_group:
            return json.dumps(
                {
                    "provider": "aws-cloudwatch-logs",
                    "service": service,
                    "resource": resource,
                    "status": "not_configured",
                    "missing": "AWS_LOG_GROUP",
                },
                sort_keys=True,
            )
        try:
            response = self._factory.client("logs").filter_log_events(
                logGroupName=settings.aws_log_group,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern='"ERROR" "timeout" "checkout"',
                limit=25,
            )
            events = [
                {
                    "timestamp": item.get("timestamp"),
                    "message": item.get("message", "")[:500],
                    "log_stream_name": item.get("logStreamName"),
                }
                for item in response.get("events", [])
            ]
            payload: dict[str, Any] = {
                "provider": "aws-cloudwatch-logs",
                "service": service,
                "resource": resource,
                "log_group": settings.aws_log_group,
                "events": events,
            }
        except Exception as exc:
            classification = classify_aws_error(exc)
            payload = {
                "provider": "aws-cloudwatch-logs",
                "service": service,
                "resource": resource,
                "error": str(exc),
                "retryable": classification.retryable,
                "classification": classification.reason,
            }
        return json.dumps(payload, default=str, sort_keys=True)

    async def query_topology(self, service: str, resource: str) -> str:
        settings = get_app_settings()
        return json.dumps(
            {
                "provider": "aws-ecs",
                "service": settings.aws_ecs_service or service,
                "cluster": settings.aws_ecs_cluster or resource,
                "dependencies": ["load-balancer", "payments-api", "orders-db"],
            },
            sort_keys=True,
        )
