from __future__ import annotations

from fastapi import FastAPI

from src.observability import instrument_fastapi

app = FastAPI(
    title="operations-api",
    description="Transitional API entry point for the operations control plane.",
)
instrument_fastapi(app)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready"}
