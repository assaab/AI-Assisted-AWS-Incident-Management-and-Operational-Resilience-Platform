# AI-Assisted AWS Incident Management and Operational Resilience Platform

This project shows how an operations team can detect and recover from a failure in a critical application using one FastAPI backend and one React dashboard.

The demo simulates a checkout service that starts failing after a bad deployment on-prem. The system detects the problem, checks metrics and recent changes, identifies the likely cause, recommends a safe rollback, waits for human approval, applies the fix, and confirms that the service has recovered.

Everything is recorded for auditing and incident reporting.

The demo runs locally without an AWS account or AI API key. Real cloud actions remain disabled by default for safety.

## Demo Scenario

The worked example is a checkout service that starts returning elevated errors and latency after deployment `checkout-r43`.

```text
failure injected
-> incident created
-> telemetry, logs, topology, and deployment evidence collected
-> RCA identifies the checkout-r43 deployment regression
-> rollback to checkout-r42 is planned
-> approval is recorded with token and incident version
-> local workload adapter performs the rollback
-> business metrics verify recovery
-> incident resolves and reports are written under artifacts/latest
```

## Run It

```powershell
make demo
make verify
make scenario-checkout-failure
```

Open:

```text
UI:       http://localhost:3000
API docs: http://localhost:8080/docs
Health:   http://localhost:8080/readyz
```

The console has a **Run checkout deployment failure scenario** button for the same deterministic flow.

The primary API is consolidated for a portfolio demo:

```text
POST /alerts
GET  /incidents
POST /incidents/{id}/investigate
POST /incidents/{id}/approve
POST /incidents/{id}/execute
GET  /incidents/{id}/audit
```

## Operational Artifacts

- [Customer enablement plan](docs/customer-enablement-plan.md)
- [Operational readiness review](docs/operational-readiness-review.md)
- [Workload criticality assessment](docs/workload-criticality-assessment.md)
- [RACI](docs/raci.md)
- [Risk register](docs/risk-register.md)
- [Incident runbook](docs/incident-runbook.md)
- [Resilience game day](docs/resilience-game-day.md)
- [Post-incident review](docs/post-incident-review.md)
- [Executive status report](docs/executive-status-report.md)
- [Well-Architected gap review](docs/well-architected-gap-review.md)
- [Service improvement backlog](docs/service-improvement-backlog.md)

## Commands

```powershell
make demo                    # app stack: API, console, checkout workload, Postgres, Redis
make down                    # stop containers
make reset                   # recreate containers and volumes
make logs                    # follow stack logs
make verify                  # wait for UI and readiness endpoints
make scenario-checkout-failure
make e2e
```

## Safety Defaults

Local mode uses:

```text
DEMO_MODE=true
AGENTIC_ENABLED=false
EXECUTION_MODE=local
EXECUTE_ACTION_DRY_RUN=true
AUTH_MODE=demo
```

AWS mode is represented by `.env.aws.example` and remains dry-run by default:

```text
DEMO_MODE=false
EXECUTION_MODE=aws
EXECUTE_ACTION_DRY_RUN=true
AUTH_MODE=oidc
```

Production mode fails closed when dependencies are unavailable. In-memory fallback is allowed only in demo mode.

## Development Checks

```powershell
ruff format --check .
ruff check .
mypy src apps
pytest
cd apps/console
npm ci
npm run typecheck
npm run build
```
