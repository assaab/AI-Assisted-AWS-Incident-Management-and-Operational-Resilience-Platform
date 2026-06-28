from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from apps.api.routers.incident_store.repository import repository
from src.domain.contracts.models import ActionRequest
from src.domain.policies.engine import PolicyEngine
from src.observability import instrument_fastapi, set_request_id

app = FastAPI(title="policy-engine")
instrument_fastapi(app)
engine = PolicyEngine()


class PolicyCheckRequest(BaseModel):
    incident_id: str
    action: ActionRequest
    autonomous: bool = False


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/evaluate")
async def evaluate(request_data: PolicyCheckRequest, request: Request) -> dict[str, object]:
    set_request_id(request.headers.get("x-request-id", str(uuid4())))
    incident = await repository.get(request_data.incident_id)
    if incident is None or incident.response_plan is None:
        raise HTTPException(status_code=404, detail="incident or response plan not found")
    decision = engine.evaluate(incident.response_plan, request_data.action, request_data.autonomous)
    return decision.model_dump(mode="json")
