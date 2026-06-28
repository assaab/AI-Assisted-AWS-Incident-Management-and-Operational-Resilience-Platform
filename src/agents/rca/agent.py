from __future__ import annotations

import httpx

from src.agent_runtime.llm import StructuredLLMError, get_llm_client
from src.agent_runtime.settings import get_agent_runtime_settings
from src.agent_runtime.tracing import agent_span
from src.agents.rca.prompts import RCA_SYSTEM
from src.agents.rca.schemas import RCALLMOutput
from src.domain.contracts.models import IncidentRecord
from src.observability.logging import get_logger

_logger = get_logger("rca-agent")


class RCAAgent:
    async def run(self, incident: IncidentRecord) -> list[dict[str, object]]:
        with agent_span("rca"):
            settings = get_agent_runtime_settings()
            if not settings.agentic_enabled:
                return self._stub_run(incident)
            try:
                client = get_llm_client()
                user = self._format_user(incident)
                out = await client.complete_json(
                    system=RCA_SYSTEM,
                    user=user,
                    response_model=RCALLMOutput,
                    agent_name="rca",
                )
                hyps = [h.model_dump() for h in out.hypotheses]
                if not hyps:
                    if not settings.agentic_stub_fallback:
                        raise StructuredLLMError("LLM returned no RCA hypotheses")
                    return self._stub_run(incident)
                return hyps
            except (StructuredLLMError, OSError, httpx.HTTPError, httpx.RequestError) as exc:
                if not settings.agentic_stub_fallback:
                    raise
                _logger.warning("rca_llm_fallback", error=str(exc))
                return self._stub_run(incident)

    def _stub_run(self, incident: IncidentRecord) -> list[dict[str, object]]:
        hypotheses: list[dict[str, object]] = []
        if incident.metadata.service == "checkout-service" and any(
            "checkout-r43" in ev.summary or "deployment" in ev.summary.lower() for ev in incident.evidence
        ):
            hypotheses.append(
                {
                    "hypothesis": "Checkout deployment revision checkout-r43 introduced elevated latency and errors",
                    "confidence": 0.86,
                    "supporting_evidence_ids": [ev.evidence_id for ev in incident.evidence],
                }
            )
        if any("cpu" in ev.summary.lower() for ev in incident.evidence):
            hypotheses.append(
                {
                    "hypothesis": "CPU saturation due to traffic spike or hot loop",
                    "confidence": 0.78,
                    "supporting_evidence_ids": [ev.evidence_id for ev in incident.evidence],
                }
            )
        if not hypotheses:
            hypotheses.append(
                {
                    "hypothesis": "Application-level error causing elevated failures",
                    "confidence": 0.55,
                    "supporting_evidence_ids": [ev.evidence_id for ev in incident.evidence],
                }
            )
        return hypotheses

    def _format_user(self, incident: IncidentRecord) -> str:
        lines = [f"incident_id={incident.incident_id}", f"symptom={incident.metadata.symptom}"]
        for ev in incident.evidence:
            lines.append(f"evidence_id={ev.evidence_id} source={ev.source} summary={ev.summary}")
        return "\n".join(lines)
