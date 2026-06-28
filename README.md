# AI-Assisted AWS Incident Management and Operational Resilience Platform

## What Is This Project?

This project is a local incident-management platform that shows how an operations team can detect service errors, investigate the cause, plan a safe remediation, request approval, execute or dry-run the fix, verify recovery, and keep an audit trail.

It is designed to demonstrate operational resilience, incident coordination, policy-controlled automation, and agentic troubleshooting for business-critical workloads.

## Simple Example

Imagine a checkout service starts failing after a deployment.

The platform flow is:

```text
Alert or error detected
-> incident created
-> triage agent evaluates severity and context
-> evidence agent gathers telemetry and change data
-> RCA and change-correlation agents identify the likely cause
-> planner agent proposes remediation
-> policy engine checks safety and approval requirements
-> human approval is requested when needed
-> executor runs or dry-runs the remediation
-> verification confirms recovery
-> audit and reporting record the outcome
```

In simple terms: the system helps move from **problem detected** to **safe recovery action** with governance and evidence.

## What Will Be the Result?

After running the project, you can see:

- Incidents created from alerts.
- Agent-driven triage, evidence gathering, RCA, and planning.
- Policy decisions that block or require approval for risky actions.
- Approval records for controlled remediation.
- Execution or dry-run results.
- Audit history showing what happened and why.
- A React console for reviewing incidents and operational status.

## How to Run It

### 1. Install backend dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

### 2. Start local infrastructure

```powershell
docker compose -f docker-compose.dev.yml up -d
alembic upgrade head
```

### 3. Start backend services

```powershell
.\tests\start-backend-services.ps1
```

This starts the local APIs on ports `8001` to `8006`.

### 4. Start the web console

```powershell
cd ui\console
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Quick Check

Run this after the services are started:

```powershell
.\tests\smoke-test.ps1
```

The smoke test checks service health, incident ingestion, incident listing, audit listing, and replay scoring.

## Main Components

```text
services/      FastAPI services for ingress, routing, incidents, approvals, policy, and audit
agents/        Triage, evidence, RCA, planner, and executor agents
libs/          Shared contracts, policy, memory, observability, and runtime helpers
adapters/      Telemetry, action, ITSM, and change-feed adapters
ui/console/    React operator console
policies/      Approval and execution rules
tests/         Unit, flow, smoke, and LLM-related tests
```

## Recommended Future Structure

The executive assessment recommends gradually moving toward this cleaner structure:

```text
apps/          API, worker, and console applications
src/           Domain, workflows, agents, adapters, persistence, security
scenarios/     Demonstration incident scenarios
sample-workload/  Local checkout service used for demos
infra/         Local and AWS infrastructure
docs/          Operational readiness and executive artifacts
```

See [files/ExecutiveAssessment.md](files/ExecutiveAssessment.md) for the full assessment and roadmap.

## Current Status

This is a local development and demonstration platform. Some integrations are still stubbed, and real AWS remediation adapters are part of the recommended next phase.

