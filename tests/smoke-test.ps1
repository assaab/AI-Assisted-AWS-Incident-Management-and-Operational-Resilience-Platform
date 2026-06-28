# End-to-end smoke: Docker health, API health, alert ingest, UI-facing reads.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Test-Url {
    param([string]$Name, [string]$Url)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
            Write-Host "[ok] $Name"
            return $true
        }
    } catch {
        Write-Host "[fail] $Name : $_"
        return $false
    }
    return $false
}

Write-Host "=== Docker containers ==="
docker compose -f docker-compose.dev.yml ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: docker compose -f docker-compose.dev.yml up -d"
    exit 1
}

Write-Host "`n=== API health ==="
$ok = $true
if (-not (Test-Url "GET /livez" "http://127.0.0.1:8080/livez")) { $ok = $false }

Write-Host "`n=== Create sample alert ==="
$body = @{
    source = "smoke-test"
    severity = "warning"
    service = "smoke-service"
    resource = "pod/$(Get-Random)"
    symptom = "High CPU from smoke test"
} | ConvertTo-Json

try {
    $ing = Invoke-RestMethod -Uri "http://127.0.0.1:8080/alerts" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    Write-Host "[ok] Created incident_id: $($ing.incident_id)"
} catch {
    Write-Host "[fail] Alert ingest: $_"
    $ok = $false
}

Write-Host "`n=== Console API reads ==="
if (-not (Test-Url "GET /incidents" "http://127.0.0.1:8080/incidents")) { $ok = $false }
if (-not (Test-Url "GET /events" "http://127.0.0.1:8080/events")) { $ok = $false }
if (-not (Test-Url "GET /replay/score" "http://127.0.0.1:8080/replay/score")) { $ok = $false }

if ($ok) {
    Write-Host "`nSmoke test passed."
    exit 0
}
Write-Host "`nSmoke test had failures."
exit 1
