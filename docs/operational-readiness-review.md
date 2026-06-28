# Operational Readiness Review

## Scope

Checkout service deployment-regression response.

## Readiness Summary

| Control | Status | Evidence |
| --- | --- | --- |
| Incident intake | Ready | `/ingest` and scenario endpoint create incidents |
| Evidence collection | Ready | Metrics, logs, topology, deployment change feed |
| Remediation plan | Ready | Rollback plan generated for checkout regression |
| Human approval | Ready | Approval token, action, plan step, version, expiry checked |
| Execution | Ready | Local adapter changes workload state |
| Verification | Ready | Recovery requires healthy checkout metrics |
| Reporting | Ready | `artifacts/latest` report files generated |

## Acceptance Criteria

`make demo`, `make verify`, and `make scenario-checkout-failure` complete without cloud credentials or an LLM key.
