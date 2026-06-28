# Incident Runbook

## Trigger

Checkout error rate exceeds 1% or p95 latency exceeds 300 ms after deployment.

## Steps

1. Confirm incident severity and customer impact.
2. Collect checkout metrics, logs, topology, and recent deployment history.
3. Check whether the current revision differs from the last known healthy revision.
4. If deployment regression is the leading hypothesis, create rollback plan to `checkout-r42`.
5. Require approval from the service approver.
6. Execute rollback through the configured adapter.
7. Verify error rate below 1%, p95 latency below 300 ms, and health status true.
8. Resolve only after verification succeeds.
9. Generate post-incident and executive reports.

## Escalation

Escalate to the incident commander if verification fails, approval expires, or the adapter cannot confirm the state change.
