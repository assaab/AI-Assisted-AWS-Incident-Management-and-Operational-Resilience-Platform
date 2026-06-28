from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from apps.api.routers.approval_api.app import ApprovalPayload
from apps.api.routers.approval_api.app import app as approval_app
from apps.api.routers.audit.app import app as audit_app
from apps.api.routers.audit.store import audit_store
from apps.api.routers.incident_store.app import app as incident_store_app
from apps.api.routers.incident_store.repository import repository
from apps.api.routers.ingress.app import IngestPayload
from apps.api.routers.ingress.app import app as ingress_app
from apps.api.routers.ingress.normalizer import normalize
from apps.api.routers.policy_engine.app import app as policy_engine_app
from apps.api.routers.readiness.app import app as readiness_app
from apps.api.routers.reporting.app import app as reporting_app
from apps.api.routers.router.app import ExecutePayload, create_plan, execute_action, route_incident
from apps.api.routers.router.app import app as router_app
from src.adapters.local.checkout_client import CheckoutServiceClient
from src.agents.change_correlation.agent import ChangeCorrelationAgent
from src.agents.evidence.agent import EvidenceAgent
from src.agents.executor.agent import ExecutionAgent
from src.agents.planner.agent import RemediationPlannerAgent
from src.agents.rca.agent import RCAAgent
from src.agents.triage.agent import TriageAgent
from src.config import get_app_settings
from src.domain.contracts.models import ApprovalRecord, ExecutionTraceEntry, IncidentRecord, IncidentState
from src.observability import instrument_fastapi
from src.persistence.memory import RedisHotStateProvider
from src.reporting.incident_reports import generate_incident_report, write_incident_report
from src.workflows.incident_workflow import execute_route


class IncidentApprovalPayload(BaseModel):
    approver: str
    approved: bool = True
    reason: Optional[str] = None
    ttl_seconds: int = 900
    action_id: Optional[str] = None
    plan_step_id: Optional[str] = None


class IncidentExecutePayload(BaseModel):
    action_id: Optional[str] = None
    approval_id: Optional[str] = None
    approval_token: Optional[str] = None
    autonomous: bool = False
    dry_run: Optional[bool] = None


hot_state = RedisHotStateProvider()


app = FastAPI(
    title="Mission-Critical Operations API",
    description="Operational readiness and incident orchestration API for the checkout deployment regression demo.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
instrument_fastapi(app)

for sub_app in (
    ingress_app,
    incident_store_app,
    router_app,
    policy_engine_app,
    approval_app,
    audit_app,
    readiness_app,
    reporting_app,
):
    app.include_router(sub_app.router)


@app.get("/livez")
async def livez() -> dict[str, str]:
    return {"status": "live"}


@app.get("/readyz")
async def readyz() -> dict[str, object]:
    settings = get_app_settings()
    checks: dict[str, object] = {"demo_mode": settings.demo_mode, "execution_mode": settings.execution_mode}
    try:
        engine = create_async_engine(settings.postgres_dsn, pool_pre_ping=True)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        await engine.dispose()
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = str(exc)
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
        await client.ping()
        await client.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = str(exc)
    if settings.execution_mode == "local":
        try:
            checks["checkout"] = await CheckoutServiceClient().health()
        except Exception as exc:
            checks["checkout"] = str(exc)
    dependency_checks = {
        key: value
        for key, value in checks.items()
        if key not in {"demo_mode", "execution_mode"}
    }
    if all(value == "ok" or isinstance(value, dict) for value in dependency_checks.values()):
        return {"status": "ready", "checks": checks}
    if settings.demo_mode:
        return {"status": "degraded", "checks": checks}
    raise HTTPException(status_code=503, detail=checks)


@app.post("/alerts", response_model=IncidentRecord)
async def create_alert(payload: IngestPayload, request: Request) -> IncidentRecord:
    """Portfolio-friendly alias for ingesting an operational alert."""
    request_id = request.headers.get("x-request-id", str(uuid4()))
    incident = normalize(payload.model_dump(exclude_none=True))
    dedupe_lock_key = f"dedupe:{incident.metadata.dedupe_key}"
    first_seen = await hot_state.set_if_absent(dedupe_lock_key, incident.incident_id, expire_seconds=300)
    if not first_seen:
        existing = await repository.get_by_dedupe_key(incident.metadata.dedupe_key)
        if existing is None:
            raise HTTPException(status_code=409, detail="duplicate incident")
        await audit_store.append(
            "alert_deduplicated",
            {"incident_id": existing.incident_id, "dedupe_key": incident.metadata.dedupe_key, "request_id": request_id},
        )
        return existing
    created = await repository.upsert(incident)
    await audit_store.append(
        "alert_created",
        {"incident_id": created.incident_id, "dedupe_key": created.metadata.dedupe_key, "request_id": request_id},
    )
    return created


@app.post("/incidents/{incident_id}/investigate", response_model=IncidentRecord)
async def investigate_incident(incident_id: str, request: Request) -> IncidentRecord:
    """Run investigation and create the pending remediation plan in one app-level operation."""
    routed = await route_incident(incident_id, request)
    await create_plan(incident_id, request)
    incident = await repository.get(routed.incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found after investigation")
    return incident


@app.post("/incidents/{incident_id}/approve")
async def approve_incident(
    incident_id: str,
    payload: IncidentApprovalPayload,
    request: Request,
) -> dict[str, object]:
    incident = await repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    action_id = payload.action_id or incident.pending_approval_action_id
    if action_id is None:
        raise HTTPException(status_code=409, detail="incident has no pending action to approve")
    approval_payload = ApprovalPayload(
        approver=payload.approver,
        action_id=action_id,
        approved=payload.approved,
        reason=payload.reason,
        ttl_seconds=payload.ttl_seconds,
        plan_step_id=payload.plan_step_id or incident.pending_plan_step_id,
        expected_incident_version=incident.version,
    )
    from apps.api.routers.approval_api.app import record_approval

    return await record_approval(incident_id, approval_payload, request)


@app.post("/incidents/{incident_id}/execute")
async def execute_incident(incident_id: str, payload: IncidentExecutePayload, request: Request) -> dict[str, object]:
    incident = await repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    if incident.pending_action_graph is None or not incident.pending_action_graph.actions:
        raise HTTPException(status_code=409, detail="incident has no pending action graph")
    action = next(
        (
            item
            for item in incident.pending_action_graph.actions
            if payload.action_id is None or item.action_id == payload.action_id
        ),
        None,
    )
    if action is None:
        raise HTTPException(status_code=404, detail="pending action not found")
    if payload.dry_run is not None:
        action = action.model_copy(update={"dry_run": payload.dry_run})

    approval_id = payload.approval_id
    approval_token = payload.approval_token
    if approval_id is None:
        approval = next(
            (
                item
                for item in reversed(incident.approvals)
                if item.approved and item.action_id == action.action_id
            ),
            None,
        )
        if approval is not None:
            approval_id = approval.approval_id
            approval_token = approval.approval_token

    execute_payload = ExecutePayload(
        action=action,
        autonomous=payload.autonomous,
        approval_id=approval_id,
        approval_token=approval_token,
        expected_incident_version=incident.version,
    )
    return await execute_action(incident_id, execute_payload, request)


@app.get("/incidents/{incident_id}/audit")
async def get_incident_audit(incident_id: str, limit: int = 200) -> list[dict[str, object]]:
    events = await audit_store.list_events(limit=limit)
    filtered: list[dict[str, object]] = []
    for event in events:
        payload = event.get("payload")
        if isinstance(payload, dict) and payload.get("incident_id") == incident_id:
            filtered.append(event)
    return filtered


async def _write_checkpoint(incident: IncidentRecord, step: str) -> None:
    if step not in incident.agent_path:
        incident.agent_path.append(step)
    await repository.upsert(incident)
    await audit_store.append("workflow_checkpoint", {"incident_id": incident.incident_id, "step": step})


@app.post("/scenario/checkout-deployment-failure")
async def run_checkout_deployment_failure() -> dict[str, object]:
    client = CheckoutServiceClient()
    await client.rollback("checkout-r42")
    await client.inject_deployment_failure()
    incident = normalize(
        {
            "source": "checkout-scenario",
            "severity": "sev2",
            "service": "checkout-service",
            "resource": "checkout-service",
            "symptom": "checkout deployment regression causing elevated errors and latency",
            "raw_payload_ref": "scenario://checkout-deployment-regression",
        }
    )
    incident = await repository.upsert(incident)
    await audit_store.append("scenario_failure_injected", {"incident_id": incident.incident_id})

    routed = await execute_route(
        incident,
        TriageAgent().run,
        EvidenceAgent().run,
        ChangeCorrelationAgent().run,
        RCAAgent().run,
        _write_checkpoint,
    )
    graph = await RemediationPlannerAgent().run(routed)
    routed.pending_action_graph = graph
    routed.pending_approval_action_id = graph.actions[0].action_id if graph.actions else None
    routed.pending_plan_step_id = graph.plan_steps[0].step_id if graph.plan_steps else None
    routed.state = IncidentState.WAITING_APPROVAL
    routed.final_diagnosis = "Deployment checkout-r43 introduced elevated checkout errors and latency."
    routed = await repository.upsert(routed)

    if not graph.actions:
        raise HTTPException(status_code=500, detail="scenario planner returned no action")
    action = graph.actions[0].model_copy(update={"dry_run": False})
    approval = ApprovalRecord(
        approval_id=f"apr_{uuid4().hex[:10]}",
        action_id=action.action_id,
        plan_step_id=routed.pending_plan_step_id,
        approval_scope="action",
        expected_incident_version_at_grant=routed.version,
        approver="demo-approver",
        approved=True,
        approval_token=f"token_{uuid4().hex}",
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        reason="Deterministic scenario approval for local checkout rollback.",
    )
    routed.approvals.append(approval)
    routed.state = IncidentState.PLANNED
    routed = await repository.upsert(routed)
    await audit_store.append(
        "approval_recorded", {"incident_id": routed.incident_id, "approval_id": approval.approval_id}
    )

    routed.state = IncidentState.EXECUTING
    routed.execution_trace.entries.append(ExecutionTraceEntry(phase="act", action_id=action.action_id))
    result = await ExecutionAgent().run(action)
    verified, metrics = await client.verify_recovery()
    routed.executed_actions.append(result)
    routed.execution_trace.entries.append(
        ExecutionTraceEntry(phase="verify", action_id=action.action_id, success=verified, message="checkout_metrics")
    )
    routed.final_resolution = "Rollback to checkout-r42 restored checkout health and business KPIs."
    routed.state = IncidentState.RESOLVED if result.success and verified else IncidentState.INVESTIGATING
    routed = await repository.upsert(routed)
    await audit_store.append(
        "scenario_completed",
        {"incident_id": routed.incident_id, "success": result.success and verified, "metrics": metrics},
    )
    write_incident_report(generate_incident_report(routed, await audit_store.list_events(limit=1000)))
    return {
        "incident": routed.model_dump(mode="json"),
        "approval": approval.model_dump(mode="json"),
        "metrics": metrics,
    }


@app.post("/route-async/{incident_id}")
async def enqueue_route(incident_id: str) -> dict[str, str]:
    settings = get_app_settings()
    incident = await repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    client = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
    await client.rpush("incident-routing-jobs", f'{{"incident_id":"{incident_id}"}}')
    await client.aclose()
    await audit_store.append("worker_job_enqueued", {"incident_id": incident_id})
    return {"incident_id": incident_id, "status": "queued"}
