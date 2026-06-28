"""
End-to-end flow: POST /alerts -> investigate -> approve -> execute with live LLMs only (no stub fallback).

Requires LLM credentials: set LLM_API_KEY (and AGENTIC_ENABLED=true) in environment or repo `.env`.
Skip if missing. Run explicitly: pytest tests/test_full_agentic_llm_flow.py -v
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient, TransportError

from apps.api.main import app
from src.agent_runtime.llm import OpenAICompatibleClient, clear_llm_client_cache
from src.agent_runtime.settings import clear_agent_runtime_settings_cache, get_agent_runtime_settings
from tests.conftest import load_dotenv_into_os_environ


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _credentials_available() -> bool:
    load_dotenv_into_os_environ(_repo_root() / ".env", override=False)
    clear_agent_runtime_settings_cache()
    clear_llm_client_cache()

    s = get_agent_runtime_settings()
    return bool(s.llm_api_key) and s.agentic_enabled


@pytest.mark.integration
def test_full_flow_ingest_route_plan_uses_llm_only(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _credentials_available():
        pytest.skip("Set LLM_API_KEY and AGENTIC_ENABLED=true in .env (or environment)")

    load_dotenv_into_os_environ(_repo_root() / ".env", override=False)
    monkeypatch.setenv("AGENTIC_ENABLED", "true")
    monkeypatch.setenv("AGENTIC_STUB_FALLBACK", "false")
    clear_agent_runtime_settings_cache()
    clear_llm_client_cache()

    assert get_agent_runtime_settings().agentic_enabled is True
    assert get_agent_runtime_settings().agentic_stub_fallback is False

    llm_http_posts: list[object] = []
    original_post = OpenAICompatibleClient._post

    async def counting_post(
        self: OpenAICompatibleClient,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
    ) -> tuple[str, int]:
        llm_http_posts.append(payload)
        return await original_post(self, url, headers, payload)

    monkeypatch.setattr(OpenAICompatibleClient, "_post", counting_post)
    clear_llm_client_cache()

    async def run_flow() -> None:
        transport = ASGITransport(app=app)
        token = uuid4().hex[:8]
        symptom = f"cpu spike and error spike on checkout ({token})"

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ingest_response = await client.post(
                "/alerts",
                json={
                    "source": "webhook",
                    "severity": "critical",
                    "service": "checkout-api",
                    "resource": "k8s-checkout",
                    "symptom": symptom,
                },
            )
            assert ingest_response.status_code == 200
            incident = ingest_response.json()
            incident_id = incident["incident_id"]

            investigate_posts_before = len(llm_http_posts)
            investigate_response = await client.post(f"/incidents/{incident_id}/investigate")
            assert investigate_response.status_code == 200
            investigated = investigate_response.json()
            investigate_llm_calls = len(llm_http_posts) - investigate_posts_before
            assert investigate_llm_calls >= 5, "expected triage, evidence, change_correlation, rca, planner LLM calls"

            hypotheses = investigated.get("hypotheses") or []
            assert len(hypotheses) >= 1
            triage_blocks = [h for h in hypotheses if "triage" in h]
            assert triage_blocks, "triage agent output missing from incident"

            evidence = investigated.get("evidence") or []
            assert len(evidence) >= 1

            graph = investigated["pending_action_graph"]
            assert graph.get("actions"), "planner produced no actions"

            approval_response = await client.post(
                f"/incidents/{incident_id}/approve",
                json={
                    "approver": "oncall@example.local",
                    "action_id": graph["actions"][0]["action_id"],
                    "approved": True,
                    "reason": "validated",
                },
            )
            assert approval_response.status_code == 200

            execute_response = await client.post(
                f"/incidents/{incident_id}/execute",
                json={
                    "action_id": graph["actions"][0]["action_id"],
                    "dry_run": True,
                },
            )
            assert execute_response.status_code == 200
            body = execute_response.json()
            assert body["result"]["success"] is True

            assert len(llm_http_posts) >= 5

    try:
        asyncio.run(run_flow())
    except TransportError as exc:
        pytest.skip(f"LLM endpoint is not reachable: {exc}")
