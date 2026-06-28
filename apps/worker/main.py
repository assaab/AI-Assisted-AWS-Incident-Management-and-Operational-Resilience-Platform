from __future__ import annotations

import asyncio
import json

import redis.asyncio as redis

from apps.api.routers.audit.store import audit_store
from apps.api.routers.incident_store.repository import repository
from src.agents.change_correlation.agent import ChangeCorrelationAgent
from src.agents.evidence.agent import EvidenceAgent
from src.agents.rca.agent import RCAAgent
from src.agents.triage.agent import TriageAgent
from src.config import get_app_settings
from src.domain.contracts.models import IncidentRecord
from src.observability.logging import get_logger
from src.workflows.incident_workflow import execute_route

logger = get_logger("workflow-worker")


async def _write_checkpoint(incident: IncidentRecord, step: str) -> None:
    if step not in incident.agent_path:
        incident.agent_path.append(step)
    await repository.upsert(incident)
    await audit_store.append("workflow_checkpoint", {"incident_id": incident.incident_id, "step": step, "worker": True})


async def _process_incident(incident_id: str) -> None:
    incident = await repository.get(incident_id)
    if incident is None:
        await audit_store.append("worker_job_failed", {"incident_id": incident_id, "reason": "incident_not_found"})
        return
    updated = await execute_route(
        incident,
        TriageAgent().run,
        EvidenceAgent().run,
        ChangeCorrelationAgent().run,
        RCAAgent().run,
        _write_checkpoint,
    )
    await audit_store.append("worker_job_completed", {"incident_id": updated.incident_id, "state": updated.state.value})


async def run_forever() -> None:
    settings = get_app_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
    logger.info("workflow_worker_started")
    while True:
        item = await client.blpop("incident-routing-jobs", timeout=5)
        if item is None:
            continue
        _, payload = item
        try:
            decoded = json.loads(payload)
            incident_id = str(decoded["incident_id"])
            await _process_incident(incident_id)
        except Exception as exc:
            logger.exception("workflow_worker_job_failed", error=str(exc))


def main() -> None:
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
