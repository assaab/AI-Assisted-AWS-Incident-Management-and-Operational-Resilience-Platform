from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.contracts.models import IncidentRecord


@dataclass(frozen=True)
class IncidentReportBundle:
    incident_id: str
    executive_summary: str
    post_incident_review: str
    incident_timeline: list[dict[str, Any]]
    metrics: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "executive_summary": self.executive_summary,
            "post_incident_review": self.post_incident_review,
            "incident_timeline": self.incident_timeline,
            "metrics": self.metrics,
        }


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError:
        return None


def _minutes_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return round(max((end - start).total_seconds(), 0.0) / 60.0, 2)


def _incident_audit_events(incident: IncidentRecord, audit_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in audit_events:
        payload = event.get("payload", {})
        if isinstance(payload, dict) and payload.get("incident_id") == incident.incident_id:
            rows.append(event)
    return sorted(rows, key=lambda item: str(item.get("created_at", "")))


def build_incident_timeline(incident: IncidentRecord, audit_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = [
        {
            "timestamp": incident.metadata.occurred_at.isoformat(),
            "phase": "detect",
            "event": "incident_detected",
            "summary": incident.metadata.symptom,
        }
    ]
    for event in _incident_audit_events(incident, audit_events):
        timeline.append(
            {
                "timestamp": str(event.get("created_at", "")),
                "phase": "audit",
                "event": str(event.get("event_type", "")),
                "summary": json.dumps(event.get("payload", {}), default=str, sort_keys=True)[:500],
            }
        )
    for entry in incident.execution_trace.entries:
        timeline.append(
            {
                "timestamp": entry.created_at.isoformat(),
                "phase": entry.phase,
                "event": entry.action_id or entry.phase,
                "summary": entry.message,
                "success": entry.success,
            }
        )
    return sorted(timeline, key=lambda item: str(item.get("timestamp", "")))


def calculate_operational_metrics(
    incident: IncidentRecord, timeline: list[dict[str, Any]], audit_events: list[dict[str, Any]]
) -> dict[str, Any]:
    occurred = incident.metadata.occurred_at.replace(tzinfo=None)
    first_route = next(
        (_parse_datetime(item.get("timestamp")) for item in timeline if item.get("event") == "workflow_checkpoint"),
        None,
    )
    resolved = incident.updated_at.replace(tzinfo=None) if incident.state.value == "resolved" else None
    approvals = [item for item in incident.approvals if item.approved]
    approval_start = approvals[-1].created_at.replace(tzinfo=None) if approvals else None
    action_event_time = next(
        (
            _parse_datetime(item.get("created_at"))
            for item in _incident_audit_events(incident, audit_events)
            if item.get("event_type") == "action_executed"
        ),
        None,
    )
    return {
        "time_to_detect_minutes": 0.0,
        "time_to_diagnose_minutes": _minutes_between(occurred, first_route),
        "mttr_minutes": _minutes_between(occurred, resolved),
        "approval_duration_minutes": _minutes_between(approval_start, action_event_time),
        "evidence_items": len(incident.evidence),
        "evidence_coverage": incident.evidence_coverage_score,
        "executed_actions": len(incident.executed_actions),
        "successful_actions": len([item for item in incident.executed_actions if item.success]),
    }


def generate_incident_report(incident: IncidentRecord, audit_events: list[dict[str, Any]]) -> IncidentReportBundle:
    timeline = build_incident_timeline(incident, audit_events)
    metrics = calculate_operational_metrics(incident, timeline, audit_events)
    root_cause = incident.final_diagnosis or "Deployment checkout-r43 introduced elevated checkout errors and latency."
    recovery = incident.final_resolution or "Recovery has not been verified yet."
    follow_ups = incident.lessons_learned or [
        "Add a canary gate for checkout deployments.",
        "Keep rollback approval paths tested during game days.",
        "Review alert thresholds after the next checkout release.",
    ]
    mttr = metrics["mttr_minutes"] if metrics["mttr_minutes"] is not None else "n/a"
    approval_duration = metrics["approval_duration_minutes"]
    approval_text = f"{approval_duration} minutes" if approval_duration is not None else "n/a"
    executive_summary = (
        "# Executive Summary\n\n"
        f"Incident `{incident.incident_id}` affected `{incident.metadata.service}` with severity "
        f"`{incident.metadata.severity}`.\n\n"
        f"* Current state: {incident.state.value}\n"
        f"* Root cause: {root_cause}\n"
        f"* Recovery proof: {recovery}\n"
        f"* MTTR: {mttr} minutes\n"
        f"* Approval duration: {approval_text}\n"
        "* Recommendation: improve checkout deployment safety with canary validation and tested rollback paths.\n"
    )
    timeline_md = "\n".join(
        f"* {item.get('timestamp', '')} - {item.get('event', '')}: {item.get('summary', '')}" for item in timeline
    )
    follow_up_md = "\n".join(f"* {item}" for item in follow_ups)
    post_incident_review = (
        "# Post-Incident Review\n\n"
        "## Incident Timeline\n\n"
        f"{timeline_md}\n\n"
        "## Customer Impact\n\n"
        f"{incident.metadata.symptom}\n\n"
        "## Decision Log\n\n"
        f"* Router decisions recorded: {len(incident.decision_records)}\n"
        f"* Evidence items collected: {len(incident.evidence)}\n"
        f"* Actions executed: {len(incident.executed_actions)}\n\n"
        "## Root Cause\n\n"
        f"{root_cause}\n\n"
        "## Recovery Proof\n\n"
        f"{recovery}\n\n"
        "## Operational Metrics\n\n"
        f"* MTTD: {metrics['time_to_detect_minutes']} minutes\n"
        f"* MTTR: {mttr} minutes\n"
        f"* Approval duration: {approval_text}\n"
        f"* Evidence coverage: {metrics['evidence_coverage']:.0%}\n\n"
        "## Follow-Up Actions\n\n"
        f"{follow_up_md}\n\n"
        "## Service-Improvement Recommendation\n\n"
        "Adopt a checkout deployment release gate that blocks promotion when synthetic checkout success, "
        "payment timeout rate, or p95 latency violate the agreed SLO window.\n"
    )
    return IncidentReportBundle(
        incident_id=incident.incident_id,
        executive_summary=executive_summary,
        post_incident_review=post_incident_review,
        incident_timeline=timeline,
        metrics=metrics,
    )


def write_incident_report(bundle: IncidentReportBundle, artifact_dir: Path = Path("artifacts/latest")) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "executive-summary.md").write_text(bundle.executive_summary, encoding="utf-8")
    (artifact_dir / "post-incident-review.md").write_text(bundle.post_incident_review, encoding="utf-8")
    (artifact_dir / "incident-timeline.json").write_text(
        json.dumps(bundle.incident_timeline, indent=2, default=str),
        encoding="utf-8",
    )
