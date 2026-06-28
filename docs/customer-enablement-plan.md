# Customer Enablement Plan

## Workload

Checkout service for a business-critical commerce journey.

## Objectives

Restore checkout availability quickly after regressions, reduce approval latency for pre-agreed rollback actions, and make incident evidence usable by operations, application owners, and executives.

## Critical User Journeys

| Journey | Target | Verification |
| --- | --- | --- |
| Browse cart to completed checkout | p95 latency under 300 ms | Checkout business metrics |
| Payment authorization | Error rate under 1% | Logs and payment timeout counters |
| Order creation | No duplicate order writes | Synthetic transaction and audit |

## Owners

| Area | Owner | Backup |
| --- | --- | --- |
| Service ownership | Checkout application owner | Commerce engineering lead |
| Operations | On-call operator | Incident commander |
| Approval | Service approver | Operations manager |
| Platform | Resilience platform owner | SRE lead |

## Enablement Milestones

| Milestone | Status | Acceptance Criteria |
| --- | --- | --- |
| Workload criticality captured | Complete | SLO, RTO, RPO, dependencies documented |
| Alert ingestion mapped | Complete | Scenario creates a checkout incident |
| Rollback runbook agreed | Complete | Approval and rollback path tested locally |
| Recovery verification defined | Complete | Error rate and p95 latency prove recovery |
| Reporting established | Complete | Executive summary and PIR generated |

## Readiness Gaps

| Gap | Owner | Priority | Status | Verification |
| --- | --- | --- | --- | --- |
| Canary analysis is not enforced before production deploy | Checkout owner | High | Open | Add deployment gate test |
| OIDC approver identity is demo-only locally | Platform owner | Medium | Planned | Enable `AUTH_MODE=oidc` |
| AWS ECS adapter is optional and dry-run | Platform owner | Medium | Planned | Boto3 contract tests |
