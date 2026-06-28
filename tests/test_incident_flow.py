from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient

from apps.api.main import app


def test_ingest_route_plan_approve_execute_flow() -> None:
    async def run_flow() -> None:
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ingest_response = await client.post(
                "/alerts",
                json={
                    "source": "webhook",
                    "severity": "critical",
                    "service": "checkout-api",
                    "resource": "k8s-checkout",
                    "symptom": "cpu spike and error spike",
                },
            )
            assert ingest_response.status_code == 200
            incident = ingest_response.json()
            incident_id = incident["incident_id"]

            investigate_response = await client.post(f"/incidents/{incident_id}/investigate")
            assert investigate_response.status_code == 200
            investigated = investigate_response.json()
            graph = investigated["pending_action_graph"]
            action = graph["actions"][0]

            approval_response = await client.post(
                f"/incidents/{incident_id}/approve",
                json={
                    "approver": "oncall@example.local",
                    "action_id": action["action_id"],
                    "approved": True,
                    "reason": "validated runbook",
                },
            )
            assert approval_response.status_code == 200

            execute_response = await client.post(
                f"/incidents/{incident_id}/execute",
                json={
                    "action_id": action["action_id"],
                    "dry_run": True,
                },
            )
            assert execute_response.status_code == 200
            body = execute_response.json()
            assert body["result"]["success"] is True

    asyncio.run(run_flow())
