import asyncio
from datetime import datetime

from apps.api.routers.policy_engine.autonomy import qualifies_for_autonomy
from src.agents.planner.agent import RemediationPlannerAgent
from src.domain.contracts.models import IncidentEnvelope, IncidentRecord


async def _build_action_graph():
    incident = IncidentRecord(
        incident_id="inc_test",
        metadata=IncidentEnvelope(
            source="test",
            severity="sev2",
            service="checkout",
            resource="k8s/checkout",
            symptom="cpu spike",
            occurred_at=datetime.utcnow(),
            dedupe_key="k",
        ),
    )
    planner = RemediationPlannerAgent()
    return await planner.run(incident)


def test_autonomy_predicate_rejects_low_confidence():
    graph = asyncio.run(_build_action_graph())
    assert not qualifies_for_autonomy(0.6, "single service", graph)


def test_autonomy_predicate_accepts_safe_actions():
    graph = asyncio.run(_build_action_graph())
    assert qualifies_for_autonomy(0.95, "single service", graph)
