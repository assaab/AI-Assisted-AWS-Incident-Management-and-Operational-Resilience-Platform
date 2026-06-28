# Starts the unified FastAPI backend used by the console and local workflows.
# Requires: Postgres and Redis running, plus a venv activated or .venv present.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Missing $py. Run: pip install -e `".[dev]`" from the project root."
}

$env:POSTGRES_DSN = "postgresql+asyncpg://postgres:postgres@localhost:5432/sre_agent"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:CORS_ALLOW_ORIGINS = "http://localhost:5173,http://localhost:5175"

$argList = @(
    "-m", "uvicorn",
    "apps.api.main:app",
    "--host", "127.0.0.1",
    "--port", "8080"
)
Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $root -WindowStyle Minimized

Write-Host "Started unified API on http://127.0.0.1:8080."
Write-Host "Console dev proxy expects the backend on port 8080."
