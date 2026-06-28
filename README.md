# AI-Assisted AWS Incident Management and Operational Resilience Platform

Local demo of an AI-assisted SRE control plane for incident triage, evidence collection, root-cause analysis, approval-gated remediation, execution, verification, and reporting.

The current demo uses a checkout deployment regression. A bad release (`checkout-r43`) causes elevated checkout errors and latency, the platform investigates the incident, plans a rollback to `checkout-r42`, records approval, executes the local workload action, verifies recovery, and writes an incident report.

The stack runs locally by default. AWS adapters and agentic LLM execution are present, but real cloud actions are dry-run unless explicitly configured.

## What Runs

- FastAPI operations API on `http://localhost:8080`
- React SRE console on `http://localhost:3000`
- Local checkout workload on `http://localhost:8090`
- Postgres with pgvector for incident state
- Redis for hot state, idempotency, and optional worker jobs
- Optional worker, scenario, and observability compose profiles

## Quick Start

Prerequisites: Docker, Docker Compose, Python 3.11, and `make`.

```powershell
make demo
make verify
make scenario-checkout-failure
```

Then Open:

```text
Console:  http://localhost:3000
API docs: http://localhost:8080/docs
Health:   http://localhost:8080/readyz
```

The console also has a `Run checkout deployment failure scenario` button. The readiness workspace is available from the console sidebar.

## Main Commands

```powershell
make demo                    # start API, console, checkout workload, Postgres, and Redis
make down                    # stop containers
make reset                   # recreate containers and volumes
make logs                    # follow stack logs
make verify                  # wait for console and API readiness
make scenario-checkout-failure
make incident-report         # write artifacts/latest after the scenario resolves
make e2e                     # verify stack, then run the checkout scenario
```

## API Surface

Primary demo endpoints:

```text
POST /alerts
GET  /incidents
POST /incidents/{id}/investigate
POST /incidents/{id}/approve
POST /incidents/{id}/execute
GET  /incidents/{id}/audit
POST /incidents/{id}/report
GET  /readiness/workloads/checkout-service
POST /scenario/checkout-deployment-failure
```

## Safety Defaults

Local demo mode uses `.env.demo`:

```text
DEMO_MODE=true
AGENTIC_ENABLED=false
EXECUTION_MODE=local
EXECUTE_ACTION_DRY_RUN=true
AUTH_MODE=demo
AUTONOMY_KILL_SWITCH=true
PLANNER_DEFAULT_DRY_RUN=true
```

AWS mode is represented by `.env.aws.example` and remains dry-run by default:

```text
DEMO_MODE=false
EXECUTION_MODE=aws
EXECUTE_ACTION_DRY_RUN=true
AUTH_MODE=oidc
```

Production mode fails closed when required dependencies are unavailable. In-memory fallback is only allowed in demo mode.

## Development Checks

```powershell
ruff format --check .
ruff check .
mypy src apps eval
pytest
cd apps/console
npm ci
npm run typecheck
npm run build
```

## Documentation

Operational readiness, runbooks, risk review, RACI, game day, executive reporting, and backlog artifacts are indexed in [docs/README.md](docs/README.md).
