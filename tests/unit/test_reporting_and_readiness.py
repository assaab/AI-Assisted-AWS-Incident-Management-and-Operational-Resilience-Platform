from __future__ import annotations

from datetime import datetime

from src.domain.contracts.models import IncidentEnvelope, IncidentRecord, IncidentState
from src.readiness.workspace import build_checkout_readiness
from src.reporting.incident_reports import generate_incident_report


def _incident(state: IncidentState = IncidentState.RESOLVED) -> IncidentRecord:
    return IncidentRecord(
        incident_id="inc_test",
        metadata=IncidentEnvelope(
            source="test",
            severity="sev2",
            service="checkout-service",
            resource="checkout-service",
            symptom="checkout errors increased",
            occurred_at=datetime(2026, 3, 19, 12, 0, 0),
            dedupe_key="checkout:test",
        ),
        state=state,
        final_diagnosis="Deployment regression",
        final_resolution="Rollback verified by checkout KPIs",
        evidence_coverage_score=0.75,
    )


def test_generate_incident_report_contains_operational_sections() -> None:
    incident = _incident()
    bundle = generate_incident_report(
        incident,
        [
            {
                "event_type": "action_executed",
                "payload": {"incident_id": incident.incident_id},
                "created_at": "2026-03-19T12:05:00",
            }
        ],
    )

    assert bundle.incident_id == incident.incident_id
    assert "Executive Summary" in bundle.executive_summary
    assert "Incident Timeline" in bundle.post_incident_review
    assert "Service-Improvement Recommendation" in bundle.post_incident_review
    assert bundle.metrics["evidence_coverage"] == 0.75


def test_checkout_readiness_uses_live_incident_counts() -> None:
    payload = build_checkout_readiness([_incident(), _incident(IncidentState.INVESTIGATING)])

    assert payload["workload"] == "checkout-service"
    assert payload["slo_summary"]["current_incidents"] == 2
    assert payload["slo_summary"]["unresolved_incidents"] == 1
    assert payload["resilience_test_status"]["status"] == "passing"
