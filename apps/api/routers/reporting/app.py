from __future__ import annotations

from fastapi import FastAPI, HTTPException

from apps.api.routers.audit.store import audit_store
from apps.api.routers.incident_store.repository import repository
from src.reporting.incident_reports import generate_incident_report, write_incident_report

app = FastAPI(title="reporting")


@app.get("/incidents/{incident_id}/report")
async def get_incident_report(incident_id: str) -> dict[str, object]:
    incident = await repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    bundle = generate_incident_report(incident, await audit_store.list_events(limit=1000))
    return bundle.as_dict()


@app.post("/incidents/{incident_id}/report")
async def create_incident_report(incident_id: str) -> dict[str, object]:
    incident = await repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    bundle = generate_incident_report(incident, await audit_store.list_events(limit=1000))
    write_incident_report(bundle)
    await audit_store.append("incident_report_generated", {"incident_id": incident_id})
    return bundle.as_dict()
