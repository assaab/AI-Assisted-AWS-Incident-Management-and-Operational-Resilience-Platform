from __future__ import annotations

from dataclasses import asdict, dataclass

from fastapi import FastAPI
from pydantic import BaseModel, Field


@dataclass
class CheckoutState:
    revision: str = "checkout-r42"
    previous_revision: str = "checkout-r41"
    replicas: int = 3
    error_rate_percent: float = 0.1
    p95_latency_ms: float = 120.0
    healthy: bool = True
    failure_injected: bool = False


state = CheckoutState()
app = FastAPI(title="checkout-service")


class RollbackPayload(BaseModel):
    to_revision: str = "checkout-r42"


class ScalePayload(BaseModel):
    replicas: int = Field(ge=1, le=20)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok" if state.healthy else "degraded", **asdict(state)}


@app.get("/metrics/business")
async def business_metrics() -> dict[str, object]:
    return asdict(state)


@app.post("/faults/deployment-regression")
async def inject_deployment_regression() -> dict[str, object]:
    state.previous_revision = "checkout-r42"
    state.revision = "checkout-r43"
    state.error_rate_percent = 8.7
    state.p95_latency_ms = 950.0
    state.healthy = False
    state.failure_injected = True
    return asdict(state)


@app.post("/deployments/rollback")
async def rollback(payload: RollbackPayload) -> dict[str, object]:
    state.revision = payload.to_revision
    state.error_rate_percent = 0.1
    state.p95_latency_ms = 125.0
    state.healthy = True
    state.failure_injected = False
    return asdict(state)


@app.post("/operations/restart")
async def restart() -> dict[str, object]:
    return {"operation": "restart", **asdict(state)}


@app.post("/operations/scale")
async def scale(payload: ScalePayload) -> dict[str, object]:
    state.replicas = payload.replicas
    return asdict(state)


@app.post("/reset")
async def reset() -> dict[str, object]:
    global state
    state = CheckoutState()
    return asdict(state)
