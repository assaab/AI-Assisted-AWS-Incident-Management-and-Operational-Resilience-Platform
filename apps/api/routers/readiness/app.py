from __future__ import annotations

from fastapi import FastAPI, HTTPException

from apps.api.routers.incident_store.repository import repository
from src.readiness.workspace import build_checkout_readiness

app = FastAPI(title="readiness")


@app.get("/readiness/workloads/{workload}")
async def get_workload_readiness(workload: str) -> dict[str, object]:
    if workload != "checkout-service":
        raise HTTPException(status_code=404, detail="readiness workspace is available for checkout-service")
    incidents = await repository.list_recent(limit=200)
    return build_checkout_readiness(incidents)
