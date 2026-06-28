# Starts all FastAPI microservices used by the console and local workflows.
# Requires: docker compose deps up, alembic upgrade head, venv activated or .venv present.
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

$services = @(
    @{ Module = "apps.api.routers.ingress.app:app"; Port = 8001 },
    @{ Module = "apps.api.routers.incident_store.app:app"; Port = 8002 },
    @{ Module = "apps.api.routers.router.app:app"; Port = 8003 },
    @{ Module = "apps.api.routers.policy_engine.app:app"; Port = 8004 },
    @{ Module = "apps.api.routers.approval_api.app:app"; Port = 8005 },
    @{ Module = "apps.api.routers.audit.app:app"; Port = 8006 }
)

foreach ($s in $services) {
    $argList = @(
        "-m", "uvicorn",
        $s.Module,
        "--host", "127.0.0.1",
        "--port", "$($s.Port)"
    )
    Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $root -WindowStyle Minimized
    Start-Sleep -Milliseconds 400
}

Write-Host "Started uvicorn processes (minimized windows) on ports 8001-8006."
Write-Host "Console expects: incident-store 8002, router 8003, audit 8006."
