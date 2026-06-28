from __future__ import annotations

from typing import Any

from src.domain.contracts.models import IncidentRecord


def build_checkout_readiness(incidents: list[IncidentRecord]) -> dict[str, Any]:
    checkout_incidents = [item for item in incidents if item.metadata.service == "checkout-service"]
    unresolved = [item for item in checkout_incidents if item.state.value != "resolved"]
    resolved = [item for item in checkout_incidents if item.state.value == "resolved"]
    return {
        "workload": "checkout-service",
        "criticality": "business-critical customer checkout",
        "availability_target": "99.9% monthly successful checkout journey availability",
        "rto": "15 minutes",
        "rpo": "0 minutes for committed orders; payment retries must be idempotent",
        "slo_summary": {
            "checkout_success_rate": ">= 99.5%",
            "p95_latency": "< 300 ms",
            "error_rate": "< 1%",
            "current_incidents": len(checkout_incidents),
            "unresolved_incidents": len(unresolved),
        },
        "observability_readiness": {
            "status": "partial",
            "coverage": ["business KPI endpoint", "latency metric", "error-rate metric", "audit trail"],
            "gaps": ["AWS dashboard wiring pending", "synthetic checkout probes not yet enforced as release gate"],
        },
        "runbook_coverage": {
            "status": "ready-for-demo",
            "covered": ["deployment regression", "rollback approval", "post-action verification"],
            "missing": ["database outage", "regional dependency impairment"],
        },
        "open_risks": [
            {
                "id": "RISK-CHECKOUT-CANARY",
                "severity": "high",
                "owner": "application owner",
                "status": "open",
                "summary": "Checkout deployments need an automated canary gate before full promotion.",
            },
            {
                "id": "RISK-AWS-DASHBOARD",
                "severity": "medium",
                "owner": "operations",
                "status": "open",
                "summary": "AWS CloudWatch evidence is available only when AWS adapters are configured.",
            },
        ],
        "resilience_test_status": {
            "last_scenario": "checkout deployment regression",
            "resolved_runs": len(resolved),
            "status": "passing" if resolved else "not-run",
        },
        "problem_management_actions": [
            "Add checkout canary release gate.",
            "Track recurrence count for deployment-related checkout incidents.",
            "Review rollback approval latency after each game day.",
        ],
        "enablement_progress": [
            {"item": "Workload criticality documented", "status": "complete"},
            {"item": "Incident runbook documented", "status": "complete"},
            {"item": "AWS adapter configuration", "status": "in-progress"},
            {"item": "Resilience tests beyond deployment regression", "status": "planned"},
        ],
    }
